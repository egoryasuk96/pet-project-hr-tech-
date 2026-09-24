"""I2: live field validation on submit (Action Engine)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.session import get_session_factory
from app.domain.approval import ApprovalTask
from app.domain.audit import HistoryEvent
from app.domain.catalog import DictionaryItem, RequestFieldDefinition, RequestType
from app.domain.enums import FieldDataType
from app.domain.notification import Notification
from app.domain.request import Request
from tests.conftest import (
    ApiDataset,
    auth_header,
    fill_valid_vacation_fields,
    set_request_field_values,
)


def _error_code(response) -> str:
    return response.json()["error"]["code"]


def _create_draft(client: TestClient, headers: dict[str, str], type_id: int) -> int:
    response = client.post("/requests", headers=headers, json={"request_type_id": type_id})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _submit(client: TestClient, headers: dict[str, str], request_id: int, action_id: int):
    return client.post(
        f"/requests/{request_id}/actions/{action_id}",
        headers=headers,
        json={},
    )


def _task_count(request_id: int) -> int:
    session = get_session_factory()()
    try:
        return int(
            session.scalar(
                select(func.count())
                .select_from(ApprovalTask)
                .where(ApprovalTask.request_id == request_id)
            )
            or 0
        )
    finally:
        session.close()


def _history_count(request_id: int) -> int:
    session = get_session_factory()()
    try:
        return int(
            session.scalar(
                select(func.count())
                .select_from(HistoryEvent)
                .where(HistoryEvent.request_id == request_id)
            )
            or 0
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


def _request_status_code(request_id: int) -> str:
    session = get_session_factory()()
    try:
        request = session.get(Request, request_id)
        assert request is not None
        from app.domain.process import Status

        status = session.get(Status, request.status_id)
        assert status is not None
        return status.code
    finally:
        session.close()


def _add_field(
    request_type_id: int,
    *,
    code: str,
    data_type: FieldDataType,
    required: bool,
    order_no: int,
    dictionary_id: int | None = None,
) -> int:
    session = get_session_factory()()
    try:
        field = RequestFieldDefinition(
            request_type_id=request_type_id,
            code=code,
            name=code,
            data_type=data_type,
            required=required,
            order_no=order_no,
            dictionary_id=dictionary_id,
        )
        session.add(field)
        session.commit()
        session.refresh(field)
        return field.id
    finally:
        session.close()


def _certificate_item_id() -> int:
    session = get_session_factory()()
    try:
        item = session.scalar(
            select(DictionaryItem).where(DictionaryItem.code == "employment")
        )
        assert item is not None
        return item.id
    finally:
        session.close()


def test_submit_valid_vacation_ok(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    fill_valid_vacation_fields(request_id)

    response = _submit(client, emp, request_id, dataset.submit_action_id)
    assert response.status_code == 200, response.text
    assert response.json()["status"]["code"] == "in_approval"
    assert _task_count(request_id) == 1
    assert _history_count(request_id) == 2
    assert _notification_count(request_id) >= 1


def test_submit_missing_required_field_validation(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    # date_from / date_to required — leave empty

    response = _submit(client, emp, request_id, dataset.submit_action_id)
    assert response.status_code == 422
    assert _error_code(response) == "VALIDATION"
    assert _request_status_code(request_id) == "draft"
    assert _task_count(request_id) == 0
    assert _history_count(request_id) == 1
    assert _notification_count(request_id) == 0


def test_submit_required_empty_string_validation(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    set_request_field_values(
        request_id,
        {"date_from": "   ", "date_to": "2026-06-14"},
    )

    response = _submit(client, emp, request_id, dataset.submit_action_id)
    assert response.status_code == 422
    assert _error_code(response) == "VALIDATION"
    assert _request_status_code(request_id) == "draft"
    assert _task_count(request_id) == 0
    assert _history_count(request_id) == 1
    assert _notification_count(request_id) == 0


def test_submit_invalid_integer_validation(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    fill_valid_vacation_fields(request_id)
    _add_field(
        dataset.vacation_type_id,
        code="days_count",
        data_type=FieldDataType.NUMBER,
        required=True,
        order_no=90,
    )
    set_request_field_values(request_id, {"days_count": "12.5"})

    response = _submit(client, emp, request_id, dataset.submit_action_id)
    assert response.status_code == 422
    assert _error_code(response) == "VALIDATION"
    assert response.json()["error"]["details"]["reason"] == "invalid_integer"
    assert _request_status_code(request_id) == "draft"
    assert _task_count(request_id) == 0


def test_submit_invalid_date_validation(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    set_request_field_values(
        request_id,
        {"date_from": "not-a-date", "date_to": "2026-06-14"},
    )

    response = _submit(client, emp, request_id, dataset.submit_action_id)
    assert response.status_code == 422
    assert _error_code(response) == "VALIDATION"
    assert response.json()["error"]["details"]["reason"] == "invalid_date"
    assert _request_status_code(request_id) == "draft"
    assert _task_count(request_id) == 0
    assert _history_count(request_id) == 1
    assert _notification_count(request_id) == 0


def test_submit_invalid_boolean_validation(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    fill_valid_vacation_fields(request_id)
    _add_field(
        dataset.vacation_type_id,
        code="needs_hotel",
        data_type=FieldDataType.BOOLEAN,
        required=True,
        order_no=91,
    )
    set_request_field_values(request_id, {"needs_hotel": "yes"})

    response = _submit(client, emp, request_id, dataset.submit_action_id)
    assert response.status_code == 422
    assert _error_code(response) == "VALIDATION"
    assert response.json()["error"]["details"]["reason"] == "invalid_boolean"
    assert _request_status_code(request_id) == "draft"
    assert _task_count(request_id) == 0


def test_submit_dictionary_item_missing_validation(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.certificate_type_id)
    set_request_field_values(request_id, {"certificate_kind": "999999"})

    response = _submit(client, emp, request_id, dataset.submit_action_id)
    assert response.status_code == 422
    assert _error_code(response) == "VALIDATION"
    assert response.json()["error"]["details"]["reason"] == "invalid_dictionary_item"
    assert _request_status_code(request_id) == "draft"
    assert _task_count(request_id) == 0
    assert _history_count(request_id) == 1
    assert _notification_count(request_id) == 0


def test_submit_inactive_request_type_validation(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    fill_valid_vacation_fields(request_id)

    session = get_session_factory()()
    try:
        request_type = session.get(RequestType, dataset.vacation_type_id)
        assert request_type is not None
        request_type.active = False
        session.commit()
    finally:
        session.close()

    try:
        response = _submit(client, emp, request_id, dataset.submit_action_id)
        assert response.status_code == 422
        assert _error_code(response) == "VALIDATION"
        assert response.json()["error"]["details"]["reason"] == "inactive_type"
        assert _request_status_code(request_id) == "draft"
        assert _task_count(request_id) == 0
        assert _history_count(request_id) == 1
        assert _notification_count(request_id) == 0
    finally:
        session = get_session_factory()()
        try:
            request_type = session.get(RequestType, dataset.vacation_type_id)
            assert request_type is not None
            request_type.active = True
            session.commit()
        finally:
            session.close()


def test_submit_after_fixing_values_succeeds(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)

    failed = _submit(client, emp, request_id, dataset.submit_action_id)
    assert failed.status_code == 422
    assert _error_code(failed) == "VALIDATION"
    assert _task_count(request_id) == 0
    assert _history_count(request_id) == 1
    assert _notification_count(request_id) == 0

    fill_valid_vacation_fields(request_id)
    ok = _submit(client, emp, request_id, dataset.submit_action_id)
    assert ok.status_code == 200, ok.text
    assert ok.json()["status"]["code"] == "in_approval"
    assert _task_count(request_id) == 1
    assert _history_count(request_id) == 2


def test_submit_valid_certificate_dictionary_id(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.certificate_type_id)
    set_request_field_values(
        request_id,
        {"certificate_kind": str(_certificate_item_id())},
    )

    response = _submit(client, emp, request_id, dataset.submit_action_id)
    assert response.status_code == 200, response.text
    assert response.json()["status"]["code"] == "in_approval"
