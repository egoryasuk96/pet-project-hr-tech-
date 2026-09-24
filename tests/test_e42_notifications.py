"""E4.2 Notification persistence written by Action Engine (BR-29)."""

from __future__ import annotations

from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.db.session import get_session_factory
from app.domain.approval import ApprovalTask
from app.domain.audit import HistoryEvent
from app.domain.enums import ApprovalTaskStatus, NotificationEventType
from app.domain.identity import User
from app.domain.notification import Notification
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


def _notifications_for(request_id: int) -> list[Notification]:
    session = get_session_factory()()
    try:
        return list(
            session.scalars(
                select(Notification)
                .where(Notification.request_id == request_id)
                .order_by(Notification.id)
            ).all()
        )
    finally:
        session.close()


def _notification_count() -> int:
    session = get_session_factory()()
    try:
        return int(session.scalar(select(func.count()).select_from(Notification)) or 0)
    finally:
        session.close()


def _open_tasks(request_id: int) -> list[ApprovalTask]:
    session = get_session_factory()()
    try:
        return list(
            session.scalars(
                select(ApprovalTask).where(
                    ApprovalTask.request_id == request_id,
                    ApprovalTask.status == ApprovalTaskStatus.OPEN,
                )
            ).all()
        )
    finally:
        session.close()


def _completed_tasks(request_id: int) -> list[ApprovalTask]:
    session = get_session_factory()()
    try:
        return list(
            session.scalars(
                select(ApprovalTask).where(
                    ApprovalTask.request_id == request_id,
                    ApprovalTask.status == ApprovalTaskStatus.COMPLETED,
                )
            ).all()
        )
    finally:
        session.close()


def test_submit_creates_notification_for_assignee(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)

    response = _execute(client, emp, request_id, dataset.submit_action_id)
    assert response.status_code == 200, response.text

    tasks = _open_tasks(request_id)
    assert len(tasks) == 1
    notifications = _notifications_for(request_id)
    assert len(notifications) == 1
    note = notifications[0]
    assert note.event_type == NotificationEventType.REQUEST_SUBMITTED
    assert note.recipient_id == tasks[0].assignee_user_id
    assert note.recipient_id == _user_id(dataset.approver_login)
    assert note.request_id == request_id
    assert note.approval_task_id == tasks[0].id
    assert note.read is False
    assert note.text == "Новая заявка требует согласования"

    session = get_session_factory()()
    try:
        events = list(
            session.scalars(
                select(HistoryEvent).where(HistoryEvent.request_id == request_id)
            ).all()
        )
        assert len(events) == 2
        assert {e.action for e in events} == {"create", "submit"}
        submit_events = [e for e in events if e.action == "submit"]
        assert len(submit_events) == 1
    finally:
        session.close()


def test_final_approve_notifies_initiator(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    assert _execute(client, emp, request_id, dataset.submit_action_id).status_code == 200
    closed_before = _open_tasks(request_id)
    assert len(closed_before) == 1
    task_id = closed_before[0].id

    apr = auth_header(client, dataset.approver_login)
    response = _execute(client, apr, request_id, dataset.approve_action_id)
    assert response.status_code == 200, response.text

    notes = [
        n
        for n in _notifications_for(request_id)
        if n.event_type == NotificationEventType.REQUEST_APPROVED
    ]
    assert len(notes) == 1
    assert notes[0].recipient_id == _user_id(dataset.employee_login)
    assert notes[0].approval_task_id == task_id
    assert notes[0].text == "Заявка согласована"
    assert _completed_tasks(request_id)
    assert notes[0].approval_task_id == _completed_tasks(request_id)[0].id


def test_reject_notifies_initiator(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    assert _execute(client, emp, request_id, dataset.submit_action_id).status_code == 200
    task_id = _open_tasks(request_id)[0].id

    apr = auth_header(client, dataset.approver_login)
    response = _execute(
        client, apr, request_id, dataset.reject_action_id, comment="Нет"
    )
    assert response.status_code == 200, response.text

    notes = [
        n
        for n in _notifications_for(request_id)
        if n.event_type == NotificationEventType.REQUEST_REJECTED
    ]
    assert len(notes) == 1
    assert notes[0].recipient_id == _user_id(dataset.employee_login)
    assert notes[0].approval_task_id == task_id
    assert notes[0].text == "Заявка отклонена"


def test_return_notifies_initiator(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    assert _execute(client, emp, request_id, dataset.submit_action_id).status_code == 200

    apr = auth_header(client, dataset.approver_login)
    response = _execute(
        client, apr, request_id, dataset.return_action_id, comment="Доработайте"
    )
    assert response.status_code == 200, response.text

    notes = [
        n
        for n in _notifications_for(request_id)
        if n.event_type == NotificationEventType.REQUEST_RETURNED
    ]
    assert len(notes) == 1
    assert notes[0].recipient_id == _user_id(dataset.employee_login)
    assert notes[0].text == "Заявка возвращена на доработку"
    assert notes[0].approval_task_id is not None


def test_cancel_notifies_initiator_without_task(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)

    response = _execute(client, emp, request_id, dataset.cancel_action_id)
    assert response.status_code == 200, response.text

    notes = _notifications_for(request_id)
    assert len(notes) == 1
    assert notes[0].event_type == NotificationEventType.REQUEST_CANCELLED
    assert notes[0].recipient_id == _user_id(dataset.employee_login)
    assert notes[0].approval_task_id is None
    assert notes[0].text == "Заявка отменена"


def test_failed_self_approve_no_notification(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    before = _notification_count()
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
    assert _execute(client, apr, request_id, dataset.approve_action_id).status_code == 403
    assert _notification_count() == before
    assert _notifications_for(request_id) == []


def test_failed_reject_without_comment_no_notification(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    assert _execute(client, emp, request_id, dataset.submit_action_id).status_code == 200
    after_submit = len(_notifications_for(request_id))

    apr = auth_header(client, dataset.approver_login)
    assert (
        _execute(client, apr, request_id, dataset.reject_action_id, comment=" ").status_code
        == 422
    )
    assert len(_notifications_for(request_id)) == after_submit


def test_failed_action_not_allowed_no_notification(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    before = len(_notifications_for(request_id))
    assert _execute(client, emp, request_id, dataset.approve_action_id).status_code == 409
    assert len(_notifications_for(request_id)) == before


def test_notification_and_history_roll_back_together(
    client: TestClient,
    dataset: ApiDataset,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)

    def boom(_session) -> None:
        raise RuntimeError("forced failure after Notification")

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

    session = get_session_factory()()
    try:
        request = session.get(Request, request_id)
        assert request is not None
        status = session.get(Status, request.status_id)
        assert status is not None
        assert status.code == "draft"
        assert request.current_stage_id is None
        assert (
            session.scalars(
                select(ApprovalTask).where(ApprovalTask.request_id == request_id)
            ).all()
            == []
        )
        history = list(
            session.scalars(
                select(HistoryEvent)
                .where(HistoryEvent.request_id == request_id)
                .order_by(HistoryEvent.id)
            ).all()
        )
        assert [e.action for e in history] == ["create"]
        assert (
            session.scalars(
                select(Notification).where(Notification.request_id == request_id)
            ).all()
            == []
        )
    finally:
        session.close()
