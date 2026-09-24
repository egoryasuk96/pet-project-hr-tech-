"""E3.1 Target API: auth, request reads, available-actions (no Action Engine)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import get_session_factory
from app.domain.request import Request
from tests.conftest import ApiDataset, TEST_PASSWORD, auth_header


def test_login_employee(client: TestClient, dataset: ApiDataset) -> None:
    response = client.post(
        "/auth/login",
        json={"login": dataset.employee_login, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["access_token"]
    assert body["user"]["login"] == dataset.employee_login
    assert body["user"]["roles"] == ["employee"]
    assert body["user"]["full_name"]


def test_login_approver(client: TestClient, dataset: ApiDataset) -> None:
    response = client.post(
        "/auth/login",
        json={"login": dataset.approver_login, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200, response.text
    assert response.json()["user"]["roles"] == ["approver"]


def test_list_requests_empty(client: TestClient, dataset: ApiDataset) -> None:
    headers = auth_header(client, dataset.employee_login)
    response = client.get("/requests", headers=headers)
    assert response.status_code == 200, response.text
    assert response.json() == []


def test_get_request_not_found(client: TestClient, dataset: ApiDataset) -> None:
    headers = auth_header(client, dataset.employee_login)
    response = client.get("/requests/99999", headers=headers)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_available_actions_not_found(client: TestClient, dataset: ApiDataset) -> None:
    headers = auth_header(client, dataset.employee_login)
    response = client.get("/requests/99999/available-actions", headers=headers)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def _insert_request(status_id: int, initiator_login: str, type_id: int) -> int:
    session = get_session_factory()()
    try:
        from app.domain.identity import User

        user = session.scalar(select(User).where(User.login == initiator_login))
        assert user is not None
        request = Request(
            request_type_id=type_id,
            initiator_user_id=user.id,
            status_id=status_id,
            current_stage_id=None,
        )
        session.add(request)
        session.commit()
        session.refresh(request)
        return request.id
    finally:
        session.close()


def test_available_actions_draft_employee_has_submit(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    request_id = _insert_request(
        dataset.draft_status_id,
        dataset.employee_login,
        dataset.vacation_type_id,
    )
    headers = auth_header(client, dataset.employee_login)
    response = client.get(f"/requests/{request_id}/available-actions", headers=headers)
    assert response.status_code == 200, response.text
    codes = {item["code"] for item in response.json()["available_actions"]}
    assert codes == {"submit", "cancel"}


def test_available_actions_draft_approver_no_task_not_found(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    request_id = _insert_request(
        dataset.draft_status_id,
        dataset.employee_login,
        dataset.vacation_type_id,
    )
    headers = auth_header(client, dataset.approver_login)
    response = client.get(f"/requests/{request_id}/available-actions", headers=headers)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_available_actions_draft_admin_forbidden(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    request_id = _insert_request(
        dataset.draft_status_id,
        dataset.employee_login,
        dataset.vacation_type_id,
    )
    headers = auth_header(client, dataset.admin_login)
    response = client.get(f"/requests/{request_id}/available-actions", headers=headers)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_available_actions_in_approval_approver(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    from tests.conftest import fill_valid_vacation_fields

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

    headers = auth_header(client, dataset.approver_login)
    response = client.get(f"/requests/{request_id}/available-actions", headers=headers)
    assert response.status_code == 200, response.text
    codes = {item["code"] for item in response.json()["available_actions"]}
    assert codes == {"approve", "reject", "return"}


def test_available_actions_returned_employee(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    request_id = _insert_request(
        dataset.returned_status_id,
        dataset.employee_login,
        dataset.vacation_type_id,
    )
    headers = auth_header(client, dataset.employee_login)
    response = client.get(f"/requests/{request_id}/available-actions", headers=headers)
    assert response.status_code == 200, response.text
    codes = {item["code"] for item in response.json()["available_actions"]}
    assert codes == {"submit", "cancel"}


def test_get_own_request_card(client: TestClient, dataset: ApiDataset) -> None:
    request_id = _insert_request(
        dataset.draft_status_id,
        dataset.employee_login,
        dataset.vacation_type_id,
    )
    headers = auth_header(client, dataset.employee_login)
    response = client.get(f"/requests/{request_id}", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == request_id
    assert body["status"]["code"] == "draft"
    assert body["request_type"]["code"] == "vacation"
    assert body["values"] == []
    assert "value_source" not in body
    assert "field_value_versions" not in body


def test_list_requests_after_create(client: TestClient, dataset: ApiDataset) -> None:
    headers = auth_header(client, dataset.employee_login)
    created = client.post(
        "/requests",
        headers=headers,
        json={"request_type_id": dataset.vacation_type_id},
    )
    assert created.status_code == 201, created.text
    assert created.json()["status"]["code"] == "draft"

    listed = client.get("/requests", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["status"]["code"] == "draft"
    assert listed.json()[0]["request_type"]["name"]


def _submit_vacation(client: TestClient, dataset: ApiDataset) -> int:
    from tests.conftest import fill_valid_vacation_fields

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
    return request_id


def test_get_request_approver_with_task(client: TestClient, dataset: ApiDataset) -> None:
    request_id = _submit_vacation(client, dataset)
    apr = auth_header(client, dataset.approver_login)
    response = client.get(f"/requests/{request_id}", headers=apr)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == request_id
    assert body["status"]["code"] == "in_approval"
    assert body["current_stage_id"] is not None


def test_get_request_approver_without_task_not_found(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    request_id = _insert_request(
        dataset.draft_status_id,
        dataset.employee_login,
        dataset.vacation_type_id,
    )
    apr = auth_header(client, dataset.approver_login)
    response = client.get(f"/requests/{request_id}", headers=apr)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_get_request_approver_after_completed_task(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    request_id = _submit_vacation(client, dataset)
    apr = auth_header(client, dataset.approver_login)
    approve = client.post(
        f"/requests/{request_id}/actions/{dataset.approve_action_id}",
        headers=apr,
        json={},
    )
    assert approve.status_code == 200, approve.text
    assert approve.json()["status"]["code"] == "approved"

    response = client.get(f"/requests/{request_id}", headers=apr)
    assert response.status_code == 200, response.text
    assert response.json()["status"]["code"] == "approved"


def test_get_request_employee_foreign_not_found(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    request_id = _insert_request(
        dataset.draft_status_id,
        dataset.approver_login,
        dataset.vacation_type_id,
    )
    emp = auth_header(client, dataset.employee_login)
    response = client.get(f"/requests/{request_id}", headers=emp)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_get_request_admin_forbidden(client: TestClient, dataset: ApiDataset) -> None:
    request_id = _submit_vacation(client, dataset)
    adm = auth_header(client, dataset.admin_login)
    response = client.get(f"/requests/{request_id}", headers=adm)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_approver_flow_submit_card_actions_approve(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    request_id = _submit_vacation(client, dataset)
    apr = auth_header(client, dataset.approver_login)

    card = client.get(f"/requests/{request_id}", headers=apr)
    assert card.status_code == 200, card.text
    assert card.json()["status"]["code"] == "in_approval"

    actions = client.get(f"/requests/{request_id}/available-actions", headers=apr)
    assert actions.status_code == 200, actions.text
    codes = {item["code"] for item in actions.json()["available_actions"]}
    assert codes == {"approve", "reject", "return"}
    approve_id = next(
        item["id"] for item in actions.json()["available_actions"] if item["code"] == "approve"
    )

    executed = client.post(
        f"/requests/{request_id}/actions/{approve_id}",
        headers=apr,
        json={},
    )
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"]["code"] == "approved"
