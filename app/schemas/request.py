"""Employee request API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import CommentKind, RequestStatus
from app.schemas.request_type import RequestTypeRef, RequestTypeSchemaOut


class CreateRequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_type_id: UUID


class CreatedRequest(BaseModel):
    id: UUID
    request_type_id: UUID
    initiator_id: UUID
    status: Literal[RequestStatus.DRAFT]
    current_stage_number: int | None
    created_at: datetime
    updated_at: datetime


class CurrentStageOut(BaseModel):
    number: int
    name: str


class RequestListItem(BaseModel):
    id: UUID
    request_type: RequestTypeRef
    status: RequestStatus
    current_stage: CurrentStageOut | None
    created_at: datetime
    updated_at: datetime


class UserRef(BaseModel):
    id: UUID
    full_name: str


class CommentOut(BaseModel):
    id: UUID
    kind: CommentKind
    text: str
    author: UserRef
    approval_task_id: UUID | None
    created_at: datetime


class FieldValue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field_code: str
    value: str | None


class UpdateValuesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    values: list[FieldValue]


class UpdatedRequestValues(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: UUID
    status: RequestStatus
    form_schema: RequestTypeSchemaOut = Field(alias="schema")
    values: list[FieldValue]
    updated_at: datetime


class RequestCard(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: UUID
    request_type: RequestTypeRef
    initiator: UserRef
    status: RequestStatus
    current_stage: CurrentStageOut | None
    created_at: datetime
    updated_at: datetime
    form_schema: RequestTypeSchemaOut = Field(alias="schema")
    values: list[FieldValue]
    value_source: Literal["working", "submitted_version"]
    submit_number: int | None = None
    comments: list[CommentOut] = Field(default_factory=list)


class SubmitRequestResult(BaseModel):
    id: UUID
    status: Literal[RequestStatus.IN_APPROVAL]
    current_stage: CurrentStageOut
    submit_number: int
    updated_at: datetime


class CancelRequestResult(BaseModel):
    id: UUID
    status: Literal[RequestStatus.CANCELLED]
    updated_at: datetime


class CreateCommentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str


class CreatedComment(BaseModel):
    id: UUID
    request_id: UUID
    author_id: UUID
    kind: Literal[CommentKind.FREE]
    text: str
    created_at: datetime


class HistoryEventOut(BaseModel):
    id: UUID
    actor: UserRef | None
    action: str
    from_state: str | None
    to_state: str | None
    comment: str | None
    at: datetime


class FieldValueVersionOut(BaseModel):
    id: UUID
    submit_number: int
    schema_document: Any
    values_document: Any
    created_at: datetime


class RequestHistory(BaseModel):
    events: list[HistoryEventOut]
    field_value_versions: list[FieldValueVersionOut]
