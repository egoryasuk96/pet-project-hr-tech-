"""Catalog of active request types and live form schemas (Target)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import not_found
from app.domain.catalog import Dictionary, RequestFieldDefinition, RequestType
from app.schemas.request_type import RequestTypeSchemaOut, RequestTypeSummary
from app.services.schema_mapping import to_type_schema, to_type_summary


def _type_load_options() -> tuple:
    return (
        selectinload(RequestType.field_definitions)
        .selectinload(RequestFieldDefinition.dictionary)
        .selectinload(Dictionary.items),
    )


def list_active_types(session: Session) -> list[RequestTypeSummary]:
    types = session.scalars(
        select(RequestType)
        .where(RequestType.active.is_(True))
        .order_by(RequestType.name)
    ).all()
    return [to_type_summary(item) for item in types]


def get_active_type(session: Session, type_id: int) -> RequestTypeSummary:
    request_type = session.get(RequestType, type_id)
    if request_type is None or not request_type.active:
        raise not_found()
    return to_type_summary(request_type)


def get_active_type_schema(session: Session, type_id: int) -> RequestTypeSchemaOut:
    request_type = session.scalar(
        select(RequestType).options(*_type_load_options()).where(RequestType.id == type_id)
    )
    if request_type is None or not request_type.active:
        raise not_found()
    return to_type_schema(request_type)
