"""Map live RequestType configuration to API schema objects."""

from __future__ import annotations

from app.domain.catalog import RequestFieldDefinition, RequestType
from app.schemas.request_type import (
    DictionaryItemOut,
    DictionaryOut,
    RequestFieldDefinitionOut,
    RequestTypeSchemaOut,
    RequestTypeSummary,
)


def to_type_summary(request_type: RequestType) -> RequestTypeSummary:
    return RequestTypeSummary(
        id=request_type.id,
        name=request_type.name,
        description=request_type.description,
    )


def to_field_definition(field: RequestFieldDefinition) -> RequestFieldDefinitionOut:
    dictionary_out: DictionaryOut | None = None
    if field.dictionary is not None:
        items = [
            DictionaryItemOut(id=item.id, code=item.code, name=item.name)
            for item in field.dictionary.items
            if item.is_active
        ]
        dictionary_out = DictionaryOut(
            id=field.dictionary.id,
            name=field.dictionary.name,
            items=items,
        )
    return RequestFieldDefinitionOut(
        code=field.code,
        name=field.name,
        data_type=field.data_type,
        required=field.required,
        order_no=field.order_no,
        dictionary_id=field.dictionary_id,
        dictionary=dictionary_out,
    )


def to_type_schema(request_type: RequestType) -> RequestTypeSchemaOut:
    fields = sorted(request_type.field_definitions, key=lambda item: item.order_no)
    return RequestTypeSchemaOut(
        request_type_id=request_type.id,
        fields=[to_field_definition(field) for field in fields],
    )
