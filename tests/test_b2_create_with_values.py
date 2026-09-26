"""B2: POST /requests accepts optional values into request_field_values + CreatedRequest.values."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.session import get_session_factory
from app.domain.request import Request, RequestFieldValue
from tests.conftest import ApiDataset, VALID_VACATION_DATES, auth_header


def _error_code(response) -> str:
    return response.json()["error"]["code"]


def _error_details(response) -> dict:
    return response.json()["error"]["details"]


def _field_value_count(request_id: int) -> int:
    session = get_session_factory()()
    try:
        return int(
            session.scalar(
                select(func.count())
                .select_from(RequestFieldValue)
                .where(RequestFieldValue.request_id == request_id)
            )
            or 0
        )
    finally:
        session.close()


def _field_values(request_id: int) -> dict[str, str | None]:
    session = get_session_factory()()
    try:
        rows = session.scalars(
            select(RequestFieldValue).where(RequestFieldValue.request_id == request_id)
        ).all()
        return {row.field_code: row.value for row in rows}
    finally:
        session.close()


def test_create_with_values_success(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    response = client.post(
        "/requests",
        headers=emp,
        json={
            "request_type_id": dataset.vacation_type_id,
            "values": [
                {"field_code": "date_from", "value": VALID_VACATION_DATES["date_from"]},
                {"field_code": "date_to", "value": VALID_VACATION_DATES["date_to"]},
            ],
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"]["code"] == "draft"
    values_by_code = {item["field_code"]: item["value"] for item in body["values"]}
    assert values_by_code["date_from"] == VALID_VACATION_DATES["date_from"]
    assert values_by_code["date_to"] == VALID_VACATION_DATES["date_to"]
    assert _field_value_count(body["id"]) == 2
    assert _field_values(body["id"]) == dict(VALID_VACATION_DATES)


def test_create_without_values_success(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    response = client.post(
        "/requests",
        headers=emp,
        json={"request_type_id": dataset.vacation_type_id},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["values"] == []
    assert _field_value_count(body["id"]) == 0


def test_create_with_unknown_field_code(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    before = 0
    session = get_session_factory()()
    try:
        before = int(session.scalar(select(func.count()).select_from(Request)) or 0)
    finally:
        session.close()

    response = client.post(
        "/requests",
        headers=emp,
        json={
            "request_type_id": dataset.vacation_type_id,
            "values": [{"field_code": "unknown", "value": "x"}],
        },
    )
    assert response.status_code == 422, response.text
    assert _error_code(response) == "VALIDATION"
    details = _error_details(response)
    assert details["field_code"] == "unknown"
    assert details["reason"] == "unknown_field"

    session = get_session_factory()()
    try:
        after = int(session.scalar(select(func.count()).select_from(Request)) or 0)
    finally:
        session.close()
    assert after == before


def test_create_with_duplicate_field_code(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    response = client.post(
        "/requests",
        headers=emp,
        json={
            "request_type_id": dataset.vacation_type_id,
            "values": [
                {"field_code": "date_from", "value": "2026-06-01"},
                {"field_code": "date_from", "value": "2026-06-02"},
            ],
        },
    )
    assert response.status_code == 422, response.text
    assert _error_code(response) == "VALIDATION"
    details = _error_details(response)
    assert details["field_code"] == "date_from"
    assert details["reason"] == "duplicate"


def test_create_with_invalid_date(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    response = client.post(
        "/requests",
        headers=emp,
        json={
            "request_type_id": dataset.vacation_type_id,
            "values": [{"field_code": "date_from", "value": "not-a-date"}],
        },
    )
    assert response.status_code == 422, response.text
    assert _error_code(response) == "VALIDATION"
    details = _error_details(response)
    assert details["field_code"] == "date_from"
    assert details["reason"] == "invalid_date"
