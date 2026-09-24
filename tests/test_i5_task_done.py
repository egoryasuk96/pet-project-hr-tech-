"""I5: TASK_DONE when decision uses a closed ApprovalTask."""

from __future__ import annotations

from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.session import get_session_factory
from app.domain.approval import ApprovalTask
from app.domain.audit import Comment, HistoryEvent
from app.domain.enums import ApprovalTaskStatus
from app.domain.identity import User
from app.domain.notification import Notification
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
    assert _execute(client, emp, request_id, dataset.submit_action_id).status_code == 200
    return request_id


def _user_id(login: str) -> UUID:
    session = get_session_factory()()
    try:
        user = session.scalar(select(User).where(User.login == login))
        assert user is not None
        return user.id
    finally:
        session.close()


def _history_count(request_id: int, action: str | None = None) -> int:
    session = get_session_factory()()
    try:
        stmt = select(func.count()).select_from(HistoryEvent).where(
            HistoryEvent.request_id == request_id
        )
        if action is not None:
            stmt = stmt.where(HistoryEvent.action == action)
        return int(session.scalar(stmt) or 0)
    finally:
        session.close()


def _notification_count(request_id: int) -> int:
    session = get_session_factory()()
    try:
        return int(
            session.scalar(
                select(func.count())
                .select_from(Notification)
                .where(Notification.request_id == request_id)
            )
            or 0
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


def test_approve_on_completed_task_returns_task_done(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    request_id = _create_and_submit(client, dataset)
    apr = auth_header(client, dataset.approver_login)
    assert _execute(client, apr, request_id, dataset.approve_action_id).status_code == 200

    before_history = _history_count(request_id)
    before_notif = _notification_count(request_id)
    before_comments = _comment_count(request_id)

    response = _execute(client, apr, request_id, dataset.approve_action_id)
    assert response.status_code == 409
    assert _error_code(response) == "TASK_DONE"
    assert _history_count(request_id) == before_history
    assert _notification_count(request_id) == before_notif
    assert _comment_count(request_id) == before_comments
    assert _history_count(request_id, "approve") == 1


def test_reject_on_completed_task_returns_task_done(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    request_id = _create_and_submit(client, dataset)
    apr = auth_header(client, dataset.approver_login)
    assert (
        _execute(
            client, apr, request_id, dataset.reject_action_id, comment="Отклонено"
        ).status_code
        == 200
    )

    before_history = _history_count(request_id)
    before_notif = _notification_count(request_id)
    before_comments = _comment_count(request_id)

    response = _execute(
        client, apr, request_id, dataset.reject_action_id, comment="Ещё раз"
    )
    assert response.status_code == 409
    assert _error_code(response) == "TASK_DONE"
    assert _history_count(request_id) == before_history
    assert _notification_count(request_id) == before_notif
    assert _comment_count(request_id) == before_comments
    assert _history_count(request_id, "reject") == 1
    assert before_comments == 1


def test_return_on_completed_task_returns_task_done(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    request_id = _create_and_submit(client, dataset)
    apr = auth_header(client, dataset.approver_login)
    assert (
        _execute(
            client, apr, request_id, dataset.return_action_id, comment="На доработку"
        ).status_code
        == 200
    )

    before_history = _history_count(request_id)
    before_notif = _notification_count(request_id)
    before_comments = _comment_count(request_id)

    response = _execute(
        client, apr, request_id, dataset.return_action_id, comment="Повтор"
    )
    assert response.status_code == 409
    assert _error_code(response) == "TASK_DONE"
    assert _history_count(request_id) == before_history
    assert _notification_count(request_id) == before_notif
    assert _comment_count(request_id) == before_comments
    assert _history_count(request_id, "return") == 1


def test_cancelled_task_for_assignee_returns_task_done(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    request_id = _create_and_submit(client, dataset)
    session = get_session_factory()()
    try:
        task = session.scalar(
            select(ApprovalTask).where(
                ApprovalTask.request_id == request_id,
                ApprovalTask.assignee_user_id == _user_id(dataset.approver_login),
            )
        )
        assert task is not None
        task.status = ApprovalTaskStatus.CANCELLED
        session.commit()
    finally:
        session.close()

    apr = auth_header(client, dataset.approver_login)
    response = _execute(client, apr, request_id, dataset.approve_action_id)
    assert response.status_code == 409
    assert _error_code(response) == "TASK_DONE"
    assert _history_count(request_id, "approve") == 0


def test_approver_without_task_forbidden(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    emp = auth_header(client, dataset.employee_login)
    created = client.post(
        "/requests",
        headers=emp,
        json={"request_type_id": dataset.vacation_type_id},
    )
    assert created.status_code == 201, created.text
    request_id = created.json()["id"]
    fill_valid_vacation_fields(request_id)
    assert _execute(client, emp, request_id, dataset.submit_action_id).status_code == 200

    session = get_session_factory()()
    try:
        tasks = session.scalars(
            select(ApprovalTask).where(ApprovalTask.request_id == request_id)
        ).all()
        for task in tasks:
            session.delete(task)
        session.commit()
    finally:
        session.close()

    apr = auth_header(client, dataset.approver_login)
    response = _execute(client, apr, request_id, dataset.approve_action_id)
    assert response.status_code == 403
    assert _error_code(response) == "FORBIDDEN_APPROVAL"
