"""I4: decision Comment on reject/return (BR-25)."""

from __future__ import annotations

from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.db.session import get_session_factory
from app.domain.approval import ApprovalTask
from app.domain.audit import Comment, HistoryEvent
from app.domain.enums import ApprovalTaskStatus, CommentKind
from app.domain.identity import User
from app.domain.request import Request
from app.services import action_engine
from tests.conftest import ApiDataset, auth_header, fill_valid_vacation_fields


def _error_code(response) -> str:
    return response.json()["error"]["code"]


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


def _create_and_submit(client: TestClient, dataset: ApiDataset) -> int:
    emp = auth_header(client, dataset.employee_login)
    created = client.post(
        "/requests",
        headers=emp,
        json={"request_type_id": dataset.vacation_type_id},
    )
    assert created.status_code == 201, created.text
    request_id = created.json()["id"]
    fill_valid_vacation_fields(request_id)
    assert (
        _execute(client, emp, request_id, dataset.submit_action_id).status_code == 200
    )
    return request_id


def _user_id(login: str) -> UUID:
    session = get_session_factory()()
    try:
        user = session.scalar(select(User).where(User.login == login))
        assert user is not None
        return user.id
    finally:
        session.close()


def _decision_comments(request_id: int) -> list[Comment]:
    session = get_session_factory()()
    try:
        return list(
            session.scalars(
                select(Comment)
                .where(
                    Comment.request_id == request_id,
                    Comment.kind == CommentKind.DECISION,
                )
                .order_by(Comment.id)
            ).all()
        )
    finally:
        session.close()


def _comment_count(request_id: int) -> int:
    session = get_session_factory()()
    try:
        return int(
            session.scalar(
                select(func.count())
                .select_from(Comment)
                .where(Comment.request_id == request_id)
            )
            or 0
        )
    finally:
        session.close()


def _actor_task(request_id: int, assignee_login: str) -> ApprovalTask:
    session = get_session_factory()()
    try:
        assignee_id = session.scalar(
            select(User.id).where(User.login == assignee_login)
        )
        assert assignee_id is not None
        task = session.scalar(
            select(ApprovalTask).where(
                ApprovalTask.request_id == request_id,
                ApprovalTask.assignee_user_id == assignee_id,
            )
        )
        assert task is not None
        session.expunge(task)
        return task
    finally:
        session.close()


def test_reject_creates_decision_comment(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    request_id = _create_and_submit(client, dataset)
    apr = auth_header(client, dataset.approver_login)
    text = "Не согласовано"

    response = _execute(client, apr, request_id, dataset.reject_action_id, comment=text)
    assert response.status_code == 200, response.text

    comments = _decision_comments(request_id)
    assert len(comments) == 1
    comment = comments[0]
    task = _actor_task(request_id, dataset.approver_login)
    assert comment.request_id == request_id
    assert comment.author_id == _user_id(dataset.approver_login)
    assert comment.approval_task_id == task.id
    assert comment.kind == CommentKind.DECISION
    assert comment.text == text
    assert comment.created_at is not None

    assert task.status == ApprovalTaskStatus.COMPLETED
    assert task.comment == text

    session = get_session_factory()()
    try:
        history = session.scalar(
            select(HistoryEvent).where(
                HistoryEvent.request_id == request_id,
                HistoryEvent.action == "reject",
            )
        )
        assert history is not None
        assert history.comment == text
        request = session.get(Request, request_id)
        assert request is not None
        assert request.current_stage_id is not None
    finally:
        session.close()


def test_return_creates_decision_comment(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    request_id = _create_and_submit(client, dataset)
    apr = auth_header(client, dataset.approver_login)
    text = "Уточните даты"

    response = _execute(client, apr, request_id, dataset.return_action_id, comment=text)
    assert response.status_code == 200, response.text

    comments = _decision_comments(request_id)
    assert len(comments) == 1
    comment = comments[0]
    task = _actor_task(request_id, dataset.approver_login)
    assert comment.request_id == request_id
    assert comment.author_id == _user_id(dataset.approver_login)
    assert comment.approval_task_id == task.id
    assert comment.kind == CommentKind.DECISION
    assert comment.text == text

    assert task.status == ApprovalTaskStatus.COMPLETED
    assert task.comment == text

    session = get_session_factory()()
    try:
        history = session.scalar(
            select(HistoryEvent).where(
                HistoryEvent.request_id == request_id,
                HistoryEvent.action == "return",
            )
        )
        assert history is not None
        assert history.comment == text
        request = session.get(Request, request_id)
        assert request is not None
        assert request.current_stage_id is not None
    finally:
        session.close()


def test_approve_does_not_create_decision_comment(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    request_id = _create_and_submit(client, dataset)
    apr = auth_header(client, dataset.approver_login)
    assert (
        _execute(client, apr, request_id, dataset.approve_action_id).status_code == 200
    )
    assert _decision_comments(request_id) == []
    assert _comment_count(request_id) == 0


def test_reject_without_comment_no_decision_comment(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    request_id = _create_and_submit(client, dataset)
    apr = auth_header(client, dataset.approver_login)
    response = _execute(client, apr, request_id, dataset.reject_action_id)
    assert response.status_code == 422
    assert _error_code(response) == "VALIDATION"
    assert _decision_comments(request_id) == []


def test_return_without_comment_no_decision_comment(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    request_id = _create_and_submit(client, dataset)
    apr = auth_header(client, dataset.approver_login)
    response = _execute(client, apr, request_id, dataset.return_action_id, comment="  ")
    assert response.status_code == 422
    assert _error_code(response) == "VALIDATION"
    assert _decision_comments(request_id) == []


def test_failed_reject_rolls_back_decision_comment(
    client: TestClient,
    dataset: ApiDataset,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request_id = _create_and_submit(client, dataset)
    before = _comment_count(request_id)

    def boom(_session) -> None:
        raise RuntimeError("forced failure after Comment")

    monkeypatch.setattr(action_engine, "_before_commit_hook", boom)

    with pytest.raises(RuntimeError, match="forced failure"):
        session = get_session_factory()()
        try:
            user = session.scalar(
                select(User)
                .options(selectinload(User.role))
                .where(User.login == dataset.approver_login)
            )
            assert user is not None
            action_engine.execute_action(
                session,
                user,
                request_id,
                dataset.reject_action_id,
                comment="Должен откатиться",
            )
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    assert _comment_count(request_id) == before
    assert _decision_comments(request_id) == []
    session = get_session_factory()()
    try:
        request = session.get(Request, request_id)
        assert request is not None
        from app.domain.process import Status

        status = session.get(Status, request.status_id)
        assert status is not None
        assert status.code == "in_approval"
        assert not session.scalar(
            select(HistoryEvent).where(
                HistoryEvent.request_id == request_id,
                HistoryEvent.action == "reject",
            )
        )
    finally:
        session.close()
