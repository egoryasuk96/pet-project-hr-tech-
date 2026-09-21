"""Request type catalog and live form schema."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from app.domain.enums import FieldDataType


class RequestTypeSummary(BaseModel):
    id: UUID
    name: str
    description: str | None


class RequestTypeRef(BaseModel):
    id: UUID
    name: str


class DictionaryItemOut(BaseModel):
    id: UUID
    code: str
    name: str


class DictionaryOut(BaseModel):
    id: UUID
    name: str
    items: list[DictionaryItemOut]


class RequestFieldDefinitionOut(BaseModel):
    code: str
    name: str
    data_type: FieldDataType
    required: bool
    order_no: int
    dictionary_id: UUID | None
    dictionary: DictionaryOut | None = None


class RequestTypeSchemaOut(BaseModel):
    request_type_id: UUID
    fields: list[RequestFieldDefinitionOut]
