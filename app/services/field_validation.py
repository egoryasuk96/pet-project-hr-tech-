"""Validate working field values against live RequestFieldDefinition (submit)."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import inactive_type, validation
from app.domain.catalog import DictionaryItem, RequestFieldDefinition, RequestType
from app.domain.enums import FieldDataType
from app.domain.request import Request, RequestFieldValue


def validate_submit(
    session: Session,
    request: Request,
    request_type: RequestType,
) -> None:
    """Validate live RequestType + RequestFieldValue before creating ApprovalTask.

    Raises AppError ``INACTIVE_TYPE`` (409) if the type is missing/inactive;
    ``VALIDATION`` (422) for field-level failures. Does not mutate request.
    """
    live_type = session.get(RequestType, request.request_type_id)
    if live_type is None or not live_type.active:
        raise inactive_type()

    definitions = session.scalars(
        select(RequestFieldDefinition)
        .where(RequestFieldDefinition.request_type_id == live_type.id)
        .order_by(RequestFieldDefinition.order_no, RequestFieldDefinition.id)
    ).all()

    values = session.scalars(
        select(RequestFieldValue).where(RequestFieldValue.request_id == request.id)
    ).all()
    by_code = {row.field_code: row.value for row in values}

    for field in definitions:
        raw = by_code.get(field.code)
        if field.required and _is_missing(raw):
            raise validation({"field_code": field.code, "reason": "required"})
        if _is_missing(raw):
            continue
        validate_field_value(session, field, raw)


def validate_field_value(
    session: Session,
    field: RequestFieldDefinition,
    raw_value: str,
) -> str:
    """Return canonical string value or raise VALIDATION.

    Target FieldDataType: text | date | number | catalog.
    number is validated as integer; catalog value is DictionaryItem.id (int) or code.
    """
    if field.data_type == FieldDataType.TEXT:
        return raw_value

    value = raw_value.strip()

    if field.data_type == FieldDataType.DATE:
        try:
            date.fromisoformat(value)
        except ValueError as exc:
            raise validation(
                {"field_code": field.code, "reason": "invalid_date"}
            ) from exc
        return value

    if field.data_type == FieldDataType.NUMBER:
        if not _is_integer_string(value):
            raise validation({"field_code": field.code, "reason": "invalid_integer"})
        return value

    if field.data_type == FieldDataType.BOOLEAN:
        lowered = value.lower()
        if lowered not in {"true", "false"}:
            raise validation({"field_code": field.code, "reason": "invalid_boolean"})
        return lowered

    if field.data_type == FieldDataType.CATALOG:
        return _validate_catalog_value(session, field, value)

    raise validation({"field_code": field.code, "reason": "unsupported_data_type"})


def _is_missing(raw: str | None) -> bool:
    return raw is None or raw.strip() == ""


def _is_integer_string(value: str) -> bool:
    if value.startswith(("+", "-")):
        body = value[1:]
    else:
        body = value
    return body.isdigit() and body != ""


def _validate_catalog_value(
    session: Session,
    field: RequestFieldDefinition,
    value: str,
) -> str:
    if field.dictionary_id is None:
        raise validation({"field_code": field.code, "reason": "invalid_dictionary_item"})

    item: DictionaryItem | None = None
    if _is_integer_string(value):
        item = session.scalar(
            select(DictionaryItem).where(
                DictionaryItem.id == int(value),
                DictionaryItem.dictionary_id == field.dictionary_id,
                DictionaryItem.active.is_(True),
            )
        )
    if item is None:
        item = session.scalar(
            select(DictionaryItem).where(
                DictionaryItem.code == value,
                DictionaryItem.dictionary_id == field.dictionary_id,
                DictionaryItem.active.is_(True),
            )
        )
    if item is None:
        raise validation(
            {"field_code": field.code, "reason": "invalid_dictionary_item"}
        )
    return str(item.id)


def definitions_by_code(
    fields: list[RequestFieldDefinition],
) -> dict[str, RequestFieldDefinition]:
    return {field.code: field for field in fields}
