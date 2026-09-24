"""E5.1 read-only History and Notifications API."""

from __future__ import annotations

from fastapi.testclient import TestClient

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


def test_history_submit_then_approve_order_desc(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    assert _execute(client, emp, request_id, dataset.submit_action_id).status_code == 200

    apr = auth_header(client, dataset.approver_login)
    assert _execute(client, apr, request_id, dataset.approve_action_id).status_code == 200

    response = client.get(f"/requests/{request_id}/history", headers=emp)
    assert response.status_code == 200, response.text
    items = response.json()["items"]
    assert len(items) == 3
    assert items[0]["action"] == "approve"
    assert items[0]["from_state"] == "in_approval"
    assert items[0]["to_state"] == "approved"
    assert items[0]["comment"] is None
    assert items[1]["action"] == "submit"
    assert items[1]["from_state"] == "draft"
    assert items[1]["to_state"] == "in_approval"
    assert items[2]["action"] == "create"
    assert items[2]["from_state"] is None
    assert items[2]["to_state"] == "draft"
    assert items[0]["at"] >= items[1]["at"]
    assert items[1]["at"] >= items[2]["at"]


def test_history_reject_includes_comment(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    assert _execute(client, emp, request_id, dataset.submit_action_id).status_code == 200

    apr = auth_header(client, dataset.approver_login)
    assert (
        _execute(client, apr, request_id, dataset.reject_action_id, comment="Причина").status_code
        == 200
    )

    response = client.get(f"/requests/{request_id}/history", headers=emp)
    assert response.status_code == 200
    reject_events = [item for item in response.json()["items"] if item["action"] == "reject"]
    assert len(reject_events) == 1
    assert reject_events[0]["comment"] == "Причина"
    assert reject_events[0]["to_state"] == "rejected"


def test_history_return_event(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    assert _execute(client, emp, request_id, dataset.submit_action_id).status_code == 200

    apr = auth_header(client, dataset.approver_login)
    assert (
        _execute(client, apr, request_id, dataset.return_action_id, comment="Правки").status_code
        == 200
    )

    response = client.get(f"/requests/{request_id}/history", headers=apr)
    assert response.status_code == 200
    actions = [item["action"] for item in response.json()["items"]]
    assert actions[0] == "return"
    assert "submit" in actions


def test_history_not_found(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    response = client.get("/requests/99999/history", headers=emp)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_history_foreign_request_hidden(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    assert _execute(client, emp, request_id, dataset.submit_action_id).status_code == 200

    # Admin has no employee ownership and no approval task → NOT_FOUND
    adm = auth_header(client, dataset.admin_login)
    # admin is not in history_reader roles → 403 FORBIDDEN
    response = client.get(f"/requests/{request_id}/history", headers=adm)
    assert response.status_code == 403

    # Another path: employee without ownership — use approver before they get a task? 
    # Approver gets access via task after submit. Before any task on a second employee's
    # request, create another employee... we only have one employee seed.
    # Approver without task: create draft (no submit) — approver has no task.
    draft_id = _create_draft(client, emp, dataset.vacation_type_id)
    apr = auth_header(client, dataset.approver_login)
    response = client.get(f"/requests/{draft_id}/history", headers=apr)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_notifications_empty(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    response = client.get("/notifications", headers=emp)
    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_notifications_after_submit_visible_to_approver_only(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    assert _execute(client, emp, request_id, dataset.submit_action_id).status_code == 200

    apr = auth_header(client, dataset.approver_login)
    apr_notes = client.get("/notifications", headers=apr)
    assert apr_notes.status_code == 200
    items = apr_notes.json()["items"]
    assert len(items) == 1
    assert items[0]["event_type"] == "request_submitted"
    assert items[0]["request_id"] == request_id
    assert items[0]["read"] is False

    emp_notes = client.get("/notifications", headers=emp)
    assert emp_notes.status_code == 200
    assert emp_notes.json()["items"] == []


def test_notifications_after_approve_reject_return_cancel(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    emp = auth_header(client, dataset.employee_login)
    initiator_id = _create_draft(client, emp, dataset.vacation_type_id)
    assert _execute(client, emp, initiator_id, dataset.submit_action_id).status_code == 200
    apr = auth_header(client, dataset.approver_login)
    assert _execute(client, apr, initiator_id, dataset.approve_action_id).status_code == 200

    rejected_id = _create_draft(client, emp, dataset.vacation_type_id)
    assert _execute(client, emp, rejected_id, dataset.submit_action_id).status_code == 200
    assert (
        _execute(client, apr, rejected_id, dataset.reject_action_id, comment="x").status_code
        == 200
    )

    returned_id = _create_draft(client, emp, dataset.vacation_type_id)
    assert _execute(client, emp, returned_id, dataset.submit_action_id).status_code == 200
    assert (
        _execute(client, apr, returned_id, dataset.return_action_id, comment="y").status_code
        == 200
    )

    cancelled_id = _create_draft(client, emp, dataset.vacation_type_id)
    assert _execute(client, emp, cancelled_id, dataset.cancel_action_id).status_code == 200

    notes = client.get("/notifications", headers=emp)
    assert notes.status_code == 200
    types = [item["event_type"] for item in notes.json()["items"]]
    # newest first
    assert types[0] == "request_cancelled"
    assert "request_approved" in types
    assert "request_rejected" in types
    assert "request_returned" in types
    created_ats = [item["created_at"] for item in notes.json()["items"]]
    assert created_ats == sorted(created_ats, reverse=True)


def test_notifications_isolation_between_users(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    assert _execute(client, emp, request_id, dataset.cancel_action_id).status_code == 200

    emp_items = client.get("/notifications", headers=emp).json()["items"]
    assert len(emp_items) == 1
    assert emp_items[0]["event_type"] == "request_cancelled"

    apr = auth_header(client, dataset.approver_login)
    assert client.get("/notifications", headers=apr).json()["items"] == []

    adm = auth_header(client, dataset.admin_login)
    assert client.get("/notifications", headers=adm).json()["items"] == []
