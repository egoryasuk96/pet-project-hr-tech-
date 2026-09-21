"""Approval task API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import ApprovalDecision, ApprovalTaskStatus, RequestStatus
from app.schemas.request import CommentOut, CurrentStageOut, FieldValue, UserRef
from app.schemas.request_type import RequestTypeRef, RequestTypeSchemaOut


class ApprovalTaskListItem(BaseModel):
    id: UUID
    request_id: UUID
    request_type: RequestTypeRef
    stage: CurrentStageOut
    status: Literal[ApprovalTaskStatus.OPEN]
    created_at: datetime


class ApprovalTaskDetail(BaseModel):
    id: UUID
    request_id: UUID
    stage_number: int
    assignee_id: UUID
    status: ApprovalTaskStatus
    decision: ApprovalDecision | None
    value_version_id: UUID | None
    decided_at: datetime | None


class ApprovalRequestCard(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: UUID
    request_type: RequestTypeRef
    initiator: UserRef
    status: RequestStatus
    current_stage: CurrentStageOut
    created_at: datetime
    updated_at: datetime
    form_schema: RequestTypeSchemaOut = Field(alias="schema")
    values: list[FieldValue]
    value_source: Literal["submitted_version"]
    submit_number: int
    comments: list[CommentOut]


class ApprovalTaskCardResponse(BaseModel):
    task: ApprovalTaskDetail
    request: ApprovalRequestCard
    available_actions: list[Literal["approve", "return", "reject"]]


class DecisionCommentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    comment: str | None = None


class DecisionTaskOut(BaseModel):
    id: UUID
    status: Literal[ApprovalTaskStatus.COMPLETED]
    decision: ApprovalDecision
    value_version_id: UUID


class DecisionRequestOut(BaseModel):
    id: UUID
    status: RequestStatus
    current_stage: CurrentStageOut


class DecisionResult(BaseModel):
    task: DecisionTaskOut
    request: DecisionRequestOut
