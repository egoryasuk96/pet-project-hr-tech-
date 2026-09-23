"""Stage 6.1 request polish: cancel, free comments, history."""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select

from app.db.session import get_session_factory
from app.domain.audit import HistoryEvent
from tests.conftest import ApiDataset, auth_header


def _create_draft(client, headers: dict[str, str], type_id) -> str:
    response = client.post("/requests", headers=headers, json={"request_type_id": str(type_id)})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _submit_vacation(client, headers: dict[str, str], type_id) -> str:
    request_id = _create_draft(client, headers, type_id)
    patched = client.patch(
        f"/requests/{request_id}",
        headers=headers,
        json={
            "values": [
                {"field_code": "date_from", "value": "2026-10-01"},
                {"field_code": "date_to", "value": "2026-10-14"},
            ]
        },
    )
    assert patched.status_code == 200, patched.text
    submitted = client.post(f"/requests/{request_id}/submit", headers=headers)
    assert submitted.status_code == 200, submitted.text
    return request_id


def test_cancel_draft(client, dataset: ApiDataset) -> None:
    headers = auth_header(client, dataset.employee_a_login)
    request_id = _create_draft(client, headers, dataset.vacation_type_id)

    response = client.post(f"/requests/{request_id}/cancel", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == request_id
    assert body["status"] == "cancelled"

    card = client.get(f"/requests/{request_id}", headers=headers)
    assert card.json()["status"] == "cancelled"

    session = get_session_factory()()
    try:
        events = session.scalars(
            select(HistoryEvent)
            .where(HistoryEvent.request_id == request_id)
            .order_by(HistoryEvent.at.asc())
        ).all()
        actions = [event.action for event in events]
        assert "created" in actions
        assert "cancel" in actions
        cancel_event = next(event for event in events if event.action == "cancel")
        assert cancel_event.from_state == "draft"
        assert cancel_event.to_state == "cancelled"
    finally:
        session.close()


def test_cancel_returned(client, dataset: ApiDataset) -> None:
    employee = auth_header(client, dataset.employee_a_login)
    approver = auth_header(client, dataset.approver_login)
    request_id = _submit_vacation(client, employee, dataset.vacation_type_id)

    tasks = client.get("/approval-tasks", headers=approver)
    assert tasks.status_code == 200
    task_id = next(item["id"] for item in tasks.json() if item["request_id"] == request_id)

    returned = client.post(
        f"/approval-tasks/{task_id}/return",
        headers=approver,
        json={"comment": "Please fix dates"},
    )
    assert returned.status_code == 200, returned.text
    assert returned.json()["request"]["status"] == "returned"

    response = client.post(f"/requests/{request_id}/cancel", headers=employee)
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "cancelled"


def test_cancel_in_approval_is_invalid_state(client, dataset: ApiDataset) -> None:
    headers = auth_header(client, dataset.employee_a_login)
    request_id = _submit_vacation(client, headers, dataset.vacation_type_id)

    response = client.post(f"/requests/{request_id}/cancel", headers=headers)
    assert response.status_code == 409
    assert response.json()["error_code"] == "ERR_INVALID_STATE"

    card = client.get(f"/requests/{request_id}", headers=headers)
    assert card.json()["status"] == "in_approval"


def test_cancel_foreign_request_is_not_found(client, dataset: ApiDataset) -> None:
    headers_a = auth_header(client, dataset.employee_a_login)
    headers_b = auth_header(client, dataset.employee_b_login)
    request_id = _create_draft(client, headers_b, dataset.vacation_type_id)

    response = client.post(f"/requests/{request_id}/cancel", headers=headers_a)
    assert response.status_code == 404
    assert response.json()["error_code"] == "ERR_NOT_FOUND"


def test_free_comment_in_approval_appears_on_card(client, dataset: ApiDataset) -> None:
    headers = auth_header(client, dataset.employee_a_login)
    request_id = _submit_vacation(client, headers, dataset.vacation_type_id)

    response = client.post(
        f"/requests/{request_id}/comments",
        headers=headers,
        json={"text": "  Additional note  "},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["request_id"] == request_id
    assert body["kind"] == "free"
    assert body["text"] == "Additional note"
    me = client.get("/me", headers=headers).json()
    assert body["author_id"] == me["id"]

    card = client.get(f"/requests/{request_id}", headers=headers)
    assert card.status_code == 200
    comments = card.json()["comments"]
    assert len(comments) == 1
    assert comments[0]["text"] == "Additional note"
    assert comments[0]["kind"] == "free"
    assert comments[0]["author"]["id"] == me["id"]


def test_free_comment_empty_text_is_validation_error(client, dataset: ApiDataset) -> None:
    headers = auth_header(client, dataset.employee_a_login)
    request_id = _submit_vacation(client, headers, dataset.vacation_type_id)

    response = client.post(
        f"/requests/{request_id}/comments",
        headers=headers,
        json={"text": "   "},
    )
    assert response.status_code == 422
    assert response.json()["error_code"] == "ERR_VALIDATION"


def test_free_comment_in_draft_is_invalid_state(client, dataset: ApiDataset) -> None:
    headers = auth_header(client, dataset.employee_a_login)
    request_id = _create_draft(client, headers, dataset.vacation_type_id)

    response = client.post(
        f"/requests/{request_id}/comments",
        headers=headers,
        json={"text": "too early"},
    )
    assert response.status_code == 409
    assert response.json()["error_code"] == "ERR_INVALID_STATE"


def test_history_employee_chronological_with_versions(client, dataset: ApiDataset) -> None:
    headers = auth_header(client, dataset.employee_a_login)
    request_id = _submit_vacation(client, headers, dataset.vacation_type_id)

    response = client.get(f"/requests/{request_id}/history", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    actions = [event["action"] for event in body["events"]]
    assert actions == ["created", "submit"]
    assert body["events"][0]["at"] <= body["events"][1]["at"]
    assert len(body["field_value_versions"]) == 1
    assert body["field_value_versions"][0]["submit_number"] == 1


def test_history_foreign_employee_is_not_found(client, dataset: ApiDataset) -> None:
    headers_a = auth_header(client, dataset.employee_a_login)
    headers_b = auth_header(client, dataset.employee_b_login)
    request_id = _create_draft(client, headers_b, dataset.vacation_type_id)

    response = client.get(f"/requests/{request_id}/history", headers=headers_a)
    assert response.status_code == 404
    assert response.json()["error_code"] == "ERR_NOT_FOUND"


def test_history_approver_with_task(client, dataset: ApiDataset) -> None:
    employee = auth_header(client, dataset.employee_a_login)
    approver = auth_header(client, dataset.approver_login)
    request_id = _submit_vacation(client, employee, dataset.vacation_type_id)

    response = client.get(f"/requests/{request_id}/history", headers=approver)
    assert response.status_code == 200, response.text
    assert [event["action"] for event in response.json()["events"]] == ["created", "submit"]


def test_history_approver_without_task_is_not_found(client, dataset: ApiDataset) -> None:
    employee = auth_header(client, dataset.employee_a_login)
    approver = auth_header(client, dataset.approver_login)
    request_id = _create_draft(client, employee, dataset.vacation_type_id)

    response = client.get(f"/requests/{request_id}/history", headers=approver)
    assert response.status_code == 404
    assert response.json()["error_code"] == "ERR_NOT_FOUND"


def test_e2e_submit_approve_still_works(client, dataset: ApiDataset) -> None:
    employee = auth_header(client, dataset.employee_a_login)
    approver = auth_header(client, dataset.approver_login)
    request_id = _submit_vacation(client, employee, dataset.vacation_type_id)

    tasks = client.get("/approval-tasks", headers=approver)
    task_id = next(item["id"] for item in tasks.json() if item["request_id"] == request_id)

    approved = client.post(
        f"/approval-tasks/{task_id}/approve",
        headers=approver,
        json={},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["request"]["status"] == "approved"

    card = client.get(f"/requests/{request_id}", headers=employee)
    assert card.json()["status"] == "approved"

    history = client.get(f"/requests/{request_id}/history", headers=employee)
    actions = [event["action"] for event in history.json()["events"]]
    assert actions == ["created", "submit", "approve"]


def test_cancel_unknown_request_is_not_found(client, dataset: ApiDataset) -> None:
    headers = auth_header(client, dataset.employee_a_login)
    response = client.post(f"/requests/{uuid4()}/cancel", headers=headers)
    assert response.status_code == 404
    assert response.json()["error_code"] == "ERR_NOT_FOUND"
