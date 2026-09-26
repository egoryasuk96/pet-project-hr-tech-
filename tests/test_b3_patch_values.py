"""B3: PATCH /requests/{id} upserts working values in draft/returned (initiator only)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import get_session_factory
from app.domain.identity import User
from app.domain.process import Status
from app.domain.request import Request, RequestFieldValue
from tests.conftest import ApiDataset, VALID_VACATION_DATES, auth_header, fill_valid_vacation_fields


def _error_code(response) -> str:
    return response.json()["error"]["code"]


def _error_details(response) -> dict:
    return response.json()["error"]["details"]


def _field_values(request_id: int) -> dict[str, str | None]:
    session = get_session_factory()()
    try:
        rows = session.scalars(
            select(RequestFieldValue).where(RequestFieldValue.request_id == request_id)
        ).all()
        return {row.field_code: row.value for row in rows}
    finally:
        session.close()


def _create_draft(
    client: TestClient,
    headers: dict[str, str],
    type_id: int,
    values: list[dict] | None = None,
) -> int:
    body: dict = {"request_type_id": type_id}
    if values is not None:
        body["values"] = values
    response = client.post("/requests", headers=headers, json=body)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _set_status(request_id: int, status_code: str) -> None:
    session = get_session_factory()()
    try:
        status = session.scalar(select(Status).where(Status.code == status_code))
        assert status is not None
        request = session.get(Request, request_id)
        assert request is not None
        request.status_id = status.id
        session.commit()
    finally:
        session.close()


def _insert_request(status_id: int, initiator_login: str, type_id: int) -> int:
    session = get_session_factory()()
    try:
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


def test_patch_values_in_draft_success(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    response = client.patch(
        f"/requests/{request_id}",
        headers=emp,
        json={
            "values": [
                {"field_code": "date_from", "value": VALID_VACATION_DATES["date_from"]},
                {"field_code": "date_to", "value": VALID_VACATION_DATES["date_to"]},
            ]
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == request_id
    assert body["status"]["code"] == "draft"
    values_by_code = {item["field_code"]: item["value"] for item in body["values"]}
    assert values_by_code["date_from"] == VALID_VACATION_DATES["date_from"]
    assert values_by_code["date_to"] == VALID_VACATION_DATES["date_to"]
    assert _field_values(request_id) == dict(VALID_VACATION_DATES)


def test_patch_values_partial_update(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(
        client,
        emp,
        dataset.vacation_type_id,
        values=[
            {"field_code": "date_from", "value": VALID_VACATION_DATES["date_from"]},
            {"field_code": "date_to", "value": VALID_VACATION_DATES["date_to"]},
        ],
    )
    response = client.patch(
        f"/requests/{request_id}",
        headers=emp,
        json={"values": [{"field_code": "date_from", "value": "2026-07-01"}]},
    )
    assert response.status_code == 200, response.text
    assert _field_values(request_id) == {
        "date_from": "2026-07-01",
        "date_to": VALID_VACATION_DATES["date_to"],
    }


def test_patch_values_in_returned_success(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    apr = auth_header(client, dataset.approver_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    fill_valid_vacation_fields(request_id)
    assert _execute(client, emp, request_id, dataset.submit_action_id).status_code == 200
    assert (
        _execute(
            client, apr, request_id, dataset.return_action_id, comment="fix"
        ).status_code
        == 200
    )

    response = client.patch(
        f"/requests/{request_id}",
        headers=emp,
        json={"values": [{"field_code": "date_from", "value": "2026-08-01"}]},
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"]["code"] == "returned"
    assert _field_values(request_id)["date_from"] == "2026-08-01"


def test_patch_values_in_in_approval_conflict(
    client: TestClient, dataset: ApiDataset
) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    fill_valid_vacation_fields(request_id)
    assert _execute(client, emp, request_id, dataset.submit_action_id).status_code == 200

    before = _field_values(request_id)
    response = client.patch(
        f"/requests/{request_id}",
        headers=emp,
        json={"values": [{"field_code": "date_from", "value": "2026-09-01"}]},
    )
    assert response.status_code == 409, response.text
    assert _error_code(response) == "INVALID_STATE"
    assert _field_values(request_id) == before


def test_patch_values_in_approved_conflict(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    fill_valid_vacation_fields(request_id)
    _set_status(request_id, "approved")

    before = _field_values(request_id)
    response = client.patch(
        f"/requests/{request_id}",
        headers=emp,
        json={"values": [{"field_code": "date_from", "value": "2026-09-01"}]},
    )
    assert response.status_code == 409, response.text
    assert _error_code(response) == "INVALID_STATE"
    assert _field_values(request_id) == before


def test_patch_values_foreign_request_not_found(
    client: TestClient, dataset: ApiDataset
) -> None:
    request_id = _insert_request(
        dataset.draft_status_id,
        dataset.approver_login,
        dataset.vacation_type_id,
    )
    emp = auth_header(client, dataset.employee_login)
    response = client.patch(
        f"/requests/{request_id}",
        headers=emp,
        json={"values": [{"field_code": "date_from", "value": "2026-06-01"}]},
    )
    assert response.status_code == 404, response.text
    assert _error_code(response) == "NOT_FOUND"


def test_patch_values_approver_forbidden(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    apr = auth_header(client, dataset.approver_login)
    response = client.patch(
        f"/requests/{request_id}",
        headers=apr,
        json={"values": [{"field_code": "date_from", "value": "2026-06-01"}]},
    )
    assert response.status_code == 403, response.text
    assert _error_code(response) == "FORBIDDEN"


def test_patch_values_unknown_field_code(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    response = client.patch(
        f"/requests/{request_id}",
        headers=emp,
        json={"values": [{"field_code": "unknown", "value": "x"}]},
    )
    assert response.status_code == 422, response.text
    assert _error_code(response) == "VALIDATION"
    details = _error_details(response)
    assert details["field_code"] == "unknown"
    assert details["reason"] == "unknown_field"


def test_patch_values_duplicate_field_code(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    response = client.patch(
        f"/requests/{request_id}",
        headers=emp,
        json={
            "values": [
                {"field_code": "date_from", "value": "2026-06-01"},
                {"field_code": "date_from", "value": "2026-06-02"},
            ]
        },
    )
    assert response.status_code == 422, response.text
    assert _error_code(response) == "VALIDATION"
    details = _error_details(response)
    assert details["field_code"] == "date_from"
    assert details["reason"] == "duplicate"


def test_patch_values_invalid_date(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    response = client.patch(
        f"/requests/{request_id}",
        headers=emp,
        json={"values": [{"field_code": "date_from", "value": "not-a-date"}]},
    )
    assert response.status_code == 422, response.text
    assert _error_code(response) == "VALIDATION"
    details = _error_details(response)
    assert details["field_code"] == "date_from"
    assert details["reason"] == "invalid_date"


def test_patch_values_empty_values(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    response = client.patch(
        f"/requests/{request_id}",
        headers=emp,
        json={"values": []},
    )
    assert response.status_code == 422, response.text
    assert _error_code(response) == "VALIDATION"
