"""Employee request API schemas (Target E2 read models + Legacy write stubs)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import ApprovalTaskStatus, CommentKind, RequestStatus


class StatusOut(BaseModel):
    id: int
    code: str
    name: str


class RequestTypeRef(BaseModel):
    id: int
    code: str
    name: str


class StageOut(BaseModel):
    id: int
    name: str
    sequence_no: int


class CreateRequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_type_id: int


class CreatedRequest(BaseModel):
    id: int
    request_type_id: int
    initiator_user_id: UUID
    status_id: int
    status: StatusOut
    current_stage_id: int | None
    created_at: datetime
    updated_at: datetime


class RequestListItem(BaseModel):
    id: int
    request_type: RequestTypeRef
    status: StatusOut
    current_stage: StageOut | None
    created_at: datetime
    updated_at: datetime


class UserRef(BaseModel):
    id: UUID
    full_name: str


class CommentOut(BaseModel):
    id: int
    kind: CommentKind
    text: str
    author: UserRef
    approval_task_id: int | None
    created_at: datetime


class FieldValue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field_code: str
    value: str | None


class ApprovalTaskSummary(BaseModel):
    id: int
    stage_id: int
    assignee_user_id: UUID
    status: ApprovalTaskStatus
    created_at: datetime
    completed_at: datetime | None = None


class UpdateValuesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    values: list[FieldValue]


class UpdatedRequestValues(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: int
    status: StatusOut
    form_schema: dict[str, Any] = Field(alias="schema")
    values: list[FieldValue]
    updated_at: datetime


class RequestCard(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: int
    request_type: RequestTypeRef
    initiator_user_id: UUID
    initiator: UserRef
    status_id: int
    status: StatusOut
    current_stage_id: int | None
    current_stage: StageOut | None
    created_at: datetime
    updated_at: datetime
    values: list[FieldValue]
    approval_tasks: list[ApprovalTaskSummary] = Field(default_factory=list)
    comments: list[CommentOut] = Field(default_factory=list)


class ActionExecuteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    comment: str | None = None


class ActionOut(BaseModel):
    id: int
    code: str
    name: str


class AvailableActionsResponse(BaseModel):
    available_actions: list[ActionOut]


# --- Legacy / Pre-E2 response shapes kept for thin wrappers (not Target primary) ---


class CurrentStageOut(BaseModel):
    number: int
    name: str


class SubmitRequestResult(BaseModel):
    id: int
    status: Literal[RequestStatus.IN_APPROVAL]
    current_stage: CurrentStageOut
    submit_number: int
    updated_at: datetime


class CancelRequestResult(BaseModel):
    id: int
    status: Literal[RequestStatus.CANCELLED]
    updated_at: datetime


class CreateCommentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str


class CreatedComment(BaseModel):
    id: int
    request_id: int
    author_id: UUID
    kind: Literal[CommentKind.FREE]
    text: str
    created_at: datetime


class HistoryEventOut(BaseModel):
    id: int
    actor: UserRef | None
    action: str
    from_state: str | None
    to_state: str | None
    comment: str | None
    at: datetime


class RequestHistory(BaseModel):
    events: list[HistoryEventOut]
