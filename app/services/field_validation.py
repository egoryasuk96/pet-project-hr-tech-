"""Validate working field values against a live RequestFieldDefinition."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import validation
from app.domain.catalog import DictionaryItem, RequestFieldDefinition
from app.domain.enums import FieldDataType


def validate_field_value(
    session: Session,
    field: RequestFieldDefinition,
    raw_value: str | None,
) -> str | None:
    """Return a canonical string value, or None when the field is cleared.

    Required-ness is checked by the caller (submit), not on draft save.
    """
    if raw_value is None or raw_value.strip() == "":
        return None

    value = raw_value.strip() if field.data_type != FieldDataType.TEXT else raw_value

    if field.data_type == FieldDataType.TEXT:
        return raw_value

    if field.data_type == FieldDataType.DATE:
        try:
            date.fromisoformat(value)
        except ValueError as exc:
            raise validation(
                {"field_code": field.code, "reason": "invalid_date"}
            ) from exc
        return value

    if field.data_type == FieldDataType.NUMBER:
        try:
            Decimal(value)
        except InvalidOperation as exc:
            raise validation(
                {"field_code": field.code, "reason": "invalid_number"}
            ) from exc
        return value

    if field.data_type == FieldDataType.CATALOG:
        try:
            item_id = UUID(value)
        except ValueError as exc:
            raise validation(
                {"field_code": field.code, "reason": "invalid_dictionary_item"}
            ) from exc
        if field.dictionary_id is None:
            raise validation({"field_code": field.code, "reason": "invalid_dictionary_item"})
        item = session.scalar(
            select(DictionaryItem).where(
                DictionaryItem.id == item_id,
                DictionaryItem.dictionary_id == field.dictionary_id,
                DictionaryItem.is_active.is_(True),
            )
        )
        if item is None:
            raise validation(
                {"field_code": field.code, "reason": "invalid_dictionary_item"}
            )
        return str(item_id)

    raise validation({"field_code": field.code, "reason": "unsupported_data_type"})


def definitions_by_code(
    fields: list[RequestFieldDefinition],
) -> dict[str, RequestFieldDefinition]:
    return {field.code: field for field in fields}
