"""E4.1 HistoryEvent audit trail written by Action Engine."""

from __future__ import annotations

from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.errors import AppError
from app.db.session import get_session_factory
from app.domain.approval import ApprovalTask
from app.domain.audit import HistoryEvent
from app.domain.enums import ApprovalTaskStatus
from app.domain.identity import User
from app.domain.process import Status
from app.domain.request import Request
from app.domain.routing import ApprovalRoute
from app.services import action_engine
from tests.conftest import ApiDataset, auth_header


def _execute(
    client: TestClient,
    headers: dict[str, str],
    request_id: int,
    action_id: int,
    comment: str | None = None,
):
    body: dict = {}
    if comment is not None:
        body["comment"] = comment
    return client.post(
        f"/requests/{request_id}/actions/{action_id}",
        headers=headers,
        json=body,
    )


def _create_draft(client: TestClient, headers: dict[str, str], type_id: int) -> int:
    response = client.post("/requests", headers=headers, json={"request_type_id": type_id})
    assert response.status_code == 201, response.text
    request_id = response.json()["id"]
    from tests.conftest import fill_valid_vacation_fields

    fill_valid_vacation_fields(request_id)
    return request_id


def _user_id(login: str) -> UUID:
    session = get_session_factory()()
    try:
        user = session.scalar(select(User).where(User.login == login))
        assert user is not None
        return user.id
    finally:
        session.close()


def _history_for(request_id: int) -> list[HistoryEvent]:
    session = get_session_factory()()
    try:
        return list(
            session.scalars(
                select(HistoryEvent)
                .where(HistoryEvent.request_id == request_id)
                .order_by(HistoryEvent.id)
            ).all()
        )
    finally:
        session.close()


def _history_count() -> int:
    session = get_session_factory()()
    try:
        return int(session.scalar(select(func.count()).select_from(HistoryEvent)) or 0)
    finally:
        session.close()


def test_submit_writes_history(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    assert [e.action for e in _history_for(request_id)] == ["create"]

    response = _execute(client, emp, request_id, dataset.submit_action_id)
    assert response.status_code == 200, response.text

    events = _history_for(request_id)
    assert [e.action for e in events] == ["create", "submit"]
    event = events[1]
    assert event.action == "submit"
    assert event.actor_id == _user_id(dataset.employee_login)
    assert event.from_state == "draft"
    assert event.to_state == "in_approval"
    assert event.comment is None


def test_approve_writes_history(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    assert _execute(client, emp, request_id, dataset.submit_action_id).status_code == 200

    apr = auth_header(client, dataset.approver_login)
    response = _execute(client, apr, request_id, dataset.approve_action_id)
    assert response.status_code == 200, response.text

    events = [e for e in _history_for(request_id) if e.action == "approve"]
    assert len(events) == 1
    assert events[0].from_state == "in_approval"
    assert events[0].to_state == "approved"
    assert events[0].actor_id == _user_id(dataset.approver_login)
    assert events[0].comment is None


def test_reject_writes_history_with_comment(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    assert _execute(client, emp, request_id, dataset.submit_action_id).status_code == 200

    apr = auth_header(client, dataset.approver_login)
    response = _execute(
        client, apr, request_id, dataset.reject_action_id, comment="Отклонено"
    )
    assert response.status_code == 200, response.text

    events = [e for e in _history_for(request_id) if e.action == "reject"]
    assert len(events) == 1
    assert events[0].from_state == "in_approval"
    assert events[0].to_state == "rejected"
    assert events[0].comment == "Отклонено"


def test_return_writes_history_with_comment(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    assert _execute(client, emp, request_id, dataset.submit_action_id).status_code == 200

    apr = auth_header(client, dataset.approver_login)
    response = _execute(
        client, apr, request_id, dataset.return_action_id, comment="Вернуть на доработку"
    )
    assert response.status_code == 200, response.text

    events = [e for e in _history_for(request_id) if e.action == "return"]
    assert len(events) == 1
    assert events[0].from_state == "in_approval"
    assert events[0].to_state == "returned"
    assert events[0].comment == "Вернуть на доработку"


def test_cancel_writes_history(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)

    response = _execute(client, emp, request_id, dataset.cancel_action_id)
    assert response.status_code == 200, response.text

    events = _history_for(request_id)
    assert [e.action for e in events] == ["create", "cancel"]
    assert events[1].action == "cancel"
    assert events[1].from_state == "draft"
    assert events[1].to_state == "cancelled"
    assert events[1].comment is None


def test_failed_self_approve_no_history(client: TestClient, dataset: ApiDataset) -> None:
    before = _history_count()
    session = get_session_factory()()
    try:
        approver = session.scalar(
            select(User)
            .options(selectinload(User.role))
            .where(User.login == dataset.approver_login)
        )
        assert approver is not None
        route = session.scalar(
            select(ApprovalRoute)
            .options(selectinload(ApprovalRoute.stages))
            .where(ApprovalRoute.request_type_id == dataset.vacation_type_id)
        )
        assert route and route.stages
        stage = sorted(route.stages, key=lambda item: item.sequence_no)[0]
        request = Request(
            request_type_id=dataset.vacation_type_id,
            initiator_user_id=approver.id,
            status_id=dataset.in_approval_status_id,
            current_stage_id=stage.id,
        )
        session.add(request)
        session.flush()
        session.add(
            ApprovalTask(
                request_id=request.id,
                stage_id=stage.id,
                assignee_user_id=approver.id,
                status=ApprovalTaskStatus.OPEN,
            )
        )
        session.commit()
        request_id = request.id
    finally:
        session.close()

    apr = auth_header(client, dataset.approver_login)
    response = _execute(client, apr, request_id, dataset.approve_action_id)
    assert response.status_code == 403
    assert _history_count() == before
    assert _history_for(request_id) == []


def test_failed_reject_without_comment_no_history(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    assert _execute(client, emp, request_id, dataset.submit_action_id).status_code == 200
    after_submit = len(_history_for(request_id))

    apr = auth_header(client, dataset.approver_login)
    response = _execute(client, apr, request_id, dataset.reject_action_id, comment="  ")
    assert response.status_code == 422
    assert len(_history_for(request_id)) == after_submit


def test_failed_action_not_allowed_no_history(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    before = len(_history_for(request_id))

    response = _execute(client, emp, request_id, dataset.approve_action_id)
    assert response.status_code == 409
    assert len(_history_for(request_id)) == before


def test_history_rolls_back_with_request_on_commit_failure(
    client: TestClient,
    dataset: ApiDataset,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)

    def boom(_session) -> None:
        raise RuntimeError("forced failure after HistoryEvent")

    monkeypatch.setattr(action_engine, "_before_commit_hook", boom)

    with pytest.raises(RuntimeError, match="forced failure"):
        session = get_session_factory()()
        try:
            user = session.scalar(
                select(User)
                .options(selectinload(User.role))
                .where(User.login == dataset.employee_login)
            )
            assert user is not None
            action_engine.execute_action(
                session,
                user,
                request_id,
                dataset.submit_action_id,
                comment=None,
            )
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # Request still draft; no open tasks; no history
    session = get_session_factory()()
    try:
        request = session.get(Request, request_id)
        assert request is not None
        status = session.get(Status, request.status_id)
        assert status is not None
        assert status.code == "draft"
        assert request.current_stage_id is None
        open_tasks = session.scalars(
            select(ApprovalTask).where(
                ApprovalTask.request_id == request_id,
                ApprovalTask.status == ApprovalTaskStatus.OPEN,
            )
        ).all()
        assert open_tasks == []
        history = _history_for(request_id)
        assert [e.action for e in history] == ["create"]
    finally:
        session.close()
