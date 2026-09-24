"""Approval task API schemas (Legacy wrappers — Target Action Engine next)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import ApprovalDecision, ApprovalTaskStatus, RequestStatus
from app.schemas.request import CommentOut, CurrentStageOut, FieldValue, StatusOut, UserRef
from app.schemas.request_type import RequestTypeRef, RequestTypeSchemaOut


class ApprovalTaskListItem(BaseModel):
    id: int
    request_id: int
    request_type: RequestTypeRef
    stage: CurrentStageOut
    status: Literal[ApprovalTaskStatus.OPEN]
    created_at: datetime


class ApprovalTaskDetail(BaseModel):
    id: int
    request_id: int
    stage_id: int
    assignee_user_id: UUID
    status: ApprovalTaskStatus
    comment: str | None = None
    completed_at: datetime | None = None


class ApprovalRequestCard(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: int
    request_type: RequestTypeRef
    initiator: UserRef
    status: StatusOut
    current_stage: CurrentStageOut | None
    created_at: datetime
    updated_at: datetime
    form_schema: RequestTypeSchemaOut = Field(alias="schema")
    values: list[FieldValue]


class ApprovalTaskCardResponse(BaseModel):
    task: ApprovalTaskDetail
    request: ApprovalRequestCard
    available_actions: list[Literal["approve", "return", "reject"]]


class DecisionCommentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    comment: str | None = None


class DecisionTaskOut(BaseModel):
    id: int
    status: Literal[ApprovalTaskStatus.COMPLETED]


class DecisionRequestOut(BaseModel):
    id: int
    status: StatusOut | RequestStatus
    current_stage: CurrentStageOut | None


class DecisionResult(BaseModel):
    task: DecisionTaskOut
    request: DecisionRequestOut
