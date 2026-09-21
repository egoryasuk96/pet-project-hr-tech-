"""Stage 5.3 employee request API tests."""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select

from app.db.session import get_session_factory
from app.domain.approval import ApprovalTask, RouteInstance
from app.domain.request import FieldValueVersion, Request
from tests.conftest import ApiDataset, auth_header


def _create_draft(client, headers: dict[str, str], type_id) -> str:
    response = client.post("/requests", headers=headers, json={"request_type_id": str(type_id)})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_create_draft(client, dataset: ApiDataset) -> None:
    headers = auth_header(client, dataset.employee_a_login)
    response = client.post(
        "/requests",
        headers=headers,
        json={"request_type_id": str(dataset.vacation_type_id)},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "draft"
    assert body["current_stage_number"] is None
    me = client.get("/me", headers=headers).json()
    assert body["initiator_id"] == me["id"]


def test_submit_missing_required_field(client, dataset: ApiDataset) -> None:
    headers = auth_header(client, dataset.employee_a_login)
    request_id = _create_draft(client, headers, dataset.vacation_type_id)
    response = client.post(f"/requests/{request_id}/submit", headers=headers)
    assert response.status_code == 422
    assert response.json()["error_code"] == "ERR_VALIDATION"
    card = client.get(f"/requests/{request_id}", headers=headers)
    assert card.json()["status"] == "draft"


def test_patch_invalid_value_type(client, dataset: ApiDataset) -> None:
    headers = auth_header(client, dataset.employee_a_login)
    request_id = _create_draft(client, headers, dataset.vacation_type_id)
    response = client.patch(
        f"/requests/{request_id}",
        headers=headers,
        json={"values": [{"field_code": "date_from", "value": "not-a-date"}]},
    )
    assert response.status_code == 422
    assert response.json()["error_code"] == "ERR_VALIDATION"


def test_patch_nonexistent_catalog_item(client, dataset: ApiDataset) -> None:
    headers = auth_header(client, dataset.employee_a_login)
    request_id = _create_draft(client, headers, dataset.certificate_type_id)
    response = client.patch(
        f"/requests/{request_id}",
        headers=headers,
        json={"values": [{"field_code": "certificate_kind", "value": str(uuid4())}]},
    )
    assert response.status_code == 422
    assert response.json()["error_code"] == "ERR_VALIDATION"


def test_list_contains_only_current_user_requests(client, dataset: ApiDataset) -> None:
    headers_a = auth_header(client, dataset.employee_a_login)
    headers_b = auth_header(client, dataset.employee_b_login)
    id_a = _create_draft(client, headers_a, dataset.vacation_type_id)
    id_b = _create_draft(client, headers_b, dataset.vacation_type_id)

    list_a = client.get("/requests", headers=headers_a)
    assert list_a.status_code == 200
    ids_a = {item["id"] for item in list_a.json()}
    assert id_a in ids_a
    assert id_b not in ids_a


def test_get_own_request(client, dataset: ApiDataset) -> None:
    headers = auth_header(client, dataset.employee_a_login)
    request_id = _create_draft(client, headers, dataset.vacation_type_id)
    response = client.get(f"/requests/{request_id}", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == request_id
    assert body["status"] == "draft"
    assert body["value_source"] == "working"
    assert "schema" in body
    assert body["comments"] == []


def test_get_foreign_request_is_not_found(client, dataset: ApiDataset) -> None:
    headers_a = auth_header(client, dataset.employee_a_login)
    headers_b = auth_header(client, dataset.employee_b_login)
    request_id = _create_draft(client, headers_b, dataset.vacation_type_id)
    response = client.get(f"/requests/{request_id}", headers=headers_a)
    assert response.status_code == 404
    assert response.json()["error_code"] == "ERR_NOT_FOUND"


def test_edit_draft(client, dataset: ApiDataset) -> None:
    headers = auth_header(client, dataset.employee_a_login)
    request_id = _create_draft(client, headers, dataset.vacation_type_id)
    response = client.patch(
        f"/requests/{request_id}",
        headers=headers,
        json={
            "values": [
                {"field_code": "date_from", "value": "2026-10-01"},
                {"field_code": "comment", "value": "demo"},
            ]
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "draft"
    values = {item["field_code"]: item["value"] for item in body["values"]}
    assert values["date_from"] == "2026-10-01"
    assert values["comment"] == "demo"


def test_edit_non_draft_is_invalid_state(client, dataset: ApiDataset) -> None:
    headers = auth_header(client, dataset.employee_a_login)
    request_id = _create_draft(client, headers, dataset.vacation_type_id)
    filled = client.patch(
        f"/requests/{request_id}",
        headers=headers,
        json={
            "values": [
                {"field_code": "date_from", "value": "2026-10-01"},
                {"field_code": "date_to", "value": "2026-10-14"},
            ]
        },
    )
    assert filled.status_code == 200
    submitted = client.post(f"/requests/{request_id}/submit", headers=headers)
    assert submitted.status_code == 200, submitted.text

    response = client.patch(
        f"/requests/{request_id}",
        headers=headers,
        json={"values": [{"field_code": "comment", "value": "too late"}]},
    )
    assert response.status_code == 409
    assert response.json()["error_code"] == "ERR_INVALID_STATE"


def test_submit_draft(client, dataset: ApiDataset) -> None:
    headers = auth_header(client, dataset.employee_a_login)
    request_id = _create_draft(client, headers, dataset.vacation_type_id)
    client.patch(
        f"/requests/{request_id}",
        headers=headers,
        json={
            "values": [
                {"field_code": "date_from", "value": "2026-10-01"},
                {"field_code": "date_to", "value": "2026-10-14"},
            ]
        },
    )
    response = client.post(f"/requests/{request_id}/submit", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "in_approval"
    assert body["submit_number"] == 1
    assert body["current_stage"]["number"] == 1

    card = client.get(f"/requests/{request_id}", headers=headers)
    assert card.status_code == 200
    assert card.json()["value_source"] == "submitted_version"

    session = get_session_factory()()
    try:
        request = session.get(Request, request_id)
        assert request is not None
        assert request.status.value == "in_approval"
        instance = session.scalar(select(RouteInstance).where(RouteInstance.request_id == request.id))
        assert instance is not None
        version = session.scalar(
            select(FieldValueVersion).where(FieldValueVersion.request_id == request.id)
        )
        assert version is not None
        task = session.scalar(select(ApprovalTask).where(ApprovalTask.request_id == request.id))
        assert task is not None
        assert task.status.value == "open"
    finally:
        session.close()


def test_submit_foreign_request_is_not_found(client, dataset: ApiDataset) -> None:
    headers_a = auth_header(client, dataset.employee_a_login)
    headers_b = auth_header(client, dataset.employee_b_login)
    request_id = _create_draft(client, headers_b, dataset.vacation_type_id)
    response = client.post(f"/requests/{request_id}/submit", headers=headers_a)
    assert response.status_code == 404
    assert response.json()["error_code"] == "ERR_NOT_FOUND"
