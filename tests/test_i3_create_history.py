"""I3: HistoryEvent on draft create (BR-24)."""

from __future__ import annotations

from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.session import get_session_factory
from app.domain.audit import HistoryEvent
from app.domain.identity import User
from app.domain.notification import Notification
from app.domain.request import Request
from tests.conftest import ApiDataset, auth_header, fill_valid_vacation_fields


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


def test_create_draft_writes_create_history(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    emp = auth_header(client, dataset.employee_login)
    response = client.post(
        "/requests",
        headers=emp,
        json={"request_type_id": dataset.vacation_type_id},
    )
    assert response.status_code == 201, response.text
    request_id = response.json()["id"]

    events = _history_for(request_id)
    assert len(events) == 1
    event = events[0]
    assert event.action == "create"
    assert event.actor_id == _user_id(dataset.employee_login)
    assert event.request_id == request_id
    assert event.from_state is None
    assert event.to_state == "draft"
    assert event.comment is None
    assert event.at is not None

    history = client.get(f"/requests/{request_id}/history", headers=emp)
    assert history.status_code == 200, history.text
    items = history.json()["items"]
    assert len(items) == 1
    assert items[0]["action"] == "create"
    assert items[0]["actor_id"] == str(_user_id(dataset.employee_login))
    assert items[0]["from_state"] is None
    assert items[0]["to_state"] == "draft"
    assert items[0]["comment"] is None

    assert _notification_count(request_id) == 0


def test_create_then_submit_history_sequence(
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

    submit = client.post(
        f"/requests/{request_id}/actions/{dataset.submit_action_id}",
        headers=emp,
        json={},
    )
    assert submit.status_code == 200, submit.text

    events = _history_for(request_id)
    assert len(events) == 2
    assert events[0].action == "create"
    assert events[0].from_state is None
    assert events[0].to_state == "draft"
    assert events[1].action == "submit"
    assert events[1].from_state == "draft"
    assert events[1].to_state == "in_approval"


def test_failed_create_leaves_no_request_or_history(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    emp = auth_header(client, dataset.employee_login)
    before_requests = 0
    before_history = 0
    session = get_session_factory()()
    try:
        before_requests = int(session.scalar(select(func.count()).select_from(Request)) or 0)
        before_history = int(
            session.scalar(select(func.count()).select_from(HistoryEvent)) or 0
        )
    finally:
        session.close()

    response = client.post(
        "/requests",
        headers=emp,
        json={"request_type_id": 999999},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"

    session = get_session_factory()()
    try:
        after_requests = int(session.scalar(select(func.count()).select_from(Request)) or 0)
        after_history = int(
            session.scalar(select(func.count()).select_from(HistoryEvent)) or 0
        )
        assert after_requests == before_requests
        assert after_history == before_history
    finally:
        session.close()
