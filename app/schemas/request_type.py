"""Request type catalog and live form schema (Target integer IDs)."""

from __future__ import annotations

from pydantic import BaseModel

from app.domain.enums import FieldDataType


class RequestTypeSummary(BaseModel):
    id: int
    code: str
    name: str
    description: str | None


class RequestTypeRef(BaseModel):
    id: int
    code: str
    name: str


class DictionaryItemOut(BaseModel):
    id: int
    code: str
    name: str


class DictionaryOut(BaseModel):
    id: int
    name: str
    items: list[DictionaryItemOut]


class RequestFieldDefinitionOut(BaseModel):
    code: str
    name: str
    data_type: FieldDataType
    required: bool
    order_no: int
    dictionary_id: int | None
    dictionary: DictionaryOut | None = None


class RequestTypeSchemaOut(BaseModel):
    request_type_id: int
    fields: list[RequestFieldDefinitionOut]
