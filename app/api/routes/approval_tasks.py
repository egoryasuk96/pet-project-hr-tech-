"""Approval task queue, request card, and decision endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.domain.enums import RoleCode
from app.domain.identity import User
from app.schemas.approval import (
    ApprovalTaskCardResponse,
    ApprovalTaskListItem,
    DecisionCommentInput,
    DecisionResult,
)
from app.schemas.common import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, ErrorResponse
from app.services import approval_service

router = APIRouter(prefix="/approval-tasks", tags=["ApprovalTasks"])

_approver = require_roles(RoleCode.APPROVER)


@router.get(
    "",
    response_model=list[ApprovalTaskListItem],
    status_code=status.HTTP_200_OK,
    summary="List approval tasks",
    description=(
        "UC-07 / FR-APP-01 / BR-14. "
        "Returns open approval tasks assigned to the current approver. "
        "Empty queue is 200 and []."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "ERR_UNAUTHORIZED"},
        403: {"model": ErrorResponse, "description": "ERR_FORBIDDEN"},
        422: {"model": ErrorResponse, "description": "ERR_VALIDATION"},
        500: {"model": ErrorResponse, "description": "ERR_INTERNAL"},
    },
)
def list_approval_tasks(
    session: Session = Depends(get_db),
    user: User = Depends(_approver),
    page: int = Query(default=DEFAULT_PAGE, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
) -> list[ApprovalTaskListItem]:
    return approval_service.list_open_tasks(
        session,
        user,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{task_id}",
    response_model=ApprovalTaskCardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get an approval task and request card",
    description=(
        "UC-07 / FR-APP-02 / BR-14. "
        "Returns an assigned task in any status and the full snapshot-based request card. "
        "Available actions are returned only for an actionable open task."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "ERR_UNAUTHORIZED"},
        403: {
            "model": ErrorResponse,
            "description": "ERR_FORBIDDEN / ERR_FORBIDDEN_APPROVAL",
        },
        422: {"model": ErrorResponse, "description": "ERR_VALIDATION"},
        500: {"model": ErrorResponse, "description": "ERR_INTERNAL"},
    },
)
def get_approval_task(
    task_id: UUID,
    session: Session = Depends(get_db),
    user: User = Depends(_approver),
) -> ApprovalTaskCardResponse:
    return approval_service.get_task_card(session, user, task_id)


@router.post(
    "/{task_id}/approve",
    response_model=DecisionResult,
    status_code=status.HTTP_200_OK,
    summary="Approve request",
    description=(
        "UC-07 / FR-APP-03 / BR-03 / BR-21. "
        "Approves the request at the current approval stage. "
        "Only the assigned approver can approve; self-approval is forbidden."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "ERR_UNAUTHORIZED"},
        403: {
            "model": ErrorResponse,
            "description": "ERR_FORBIDDEN / ERR_FORBIDDEN_APPROVAL",
        },
        409: {
            "model": ErrorResponse,
            "description": "ERR_TASK_DONE / ERR_INVALID_STATE",
        },
        422: {"model": ErrorResponse, "description": "ERR_VALIDATION"},
        500: {"model": ErrorResponse, "description": "ERR_INTERNAL"},
    },
)
def approve_task(
    task_id: UUID,
    body: DecisionCommentInput,
    session: Session = Depends(get_db),
    user: User = Depends(_approver),
) -> DecisionResult:
    return approval_service.approve_task(session, user, task_id, body.comment)


@router.post(
    "/{task_id}/return",
    response_model=DecisionResult,
    status_code=status.HTTP_200_OK,
    summary="Return request for revision",
    description=(
        "UC-09 / FR-APP-05 / BR-05 / BR-21 / BR-25. "
        "Returns the request to the initiator for revision. "
        "Only the assigned approver can return; a non-empty comment is required."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "ERR_UNAUTHORIZED"},
        403: {
            "model": ErrorResponse,
            "description": "ERR_FORBIDDEN / ERR_FORBIDDEN_APPROVAL",
        },
        409: {
            "model": ErrorResponse,
            "description": "ERR_TASK_DONE / ERR_INVALID_STATE",
        },
        422: {"model": ErrorResponse, "description": "ERR_VALIDATION"},
        500: {"model": ErrorResponse, "description": "ERR_INTERNAL"},
    },
)
def return_task(
    task_id: UUID,
    body: DecisionCommentInput,
    session: Session = Depends(get_db),
    user: User = Depends(_approver),
) -> DecisionResult:
    return approval_service.return_task(session, user, task_id, body.comment)


@router.post(
    "/{task_id}/reject",
    response_model=DecisionResult,
    status_code=status.HTTP_200_OK,
    summary="Reject request",
    description=(
        "UC-08 / FR-APP-04 / BR-04 / BR-21 / BR-25. "
        "Rejects the request and completes its approval route. "
        "Only the assigned approver can reject; a non-empty comment is required."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "ERR_UNAUTHORIZED"},
        403: {
            "model": ErrorResponse,
            "description": "ERR_FORBIDDEN / ERR_FORBIDDEN_APPROVAL",
        },
        409: {
            "model": ErrorResponse,
            "description": "ERR_TASK_DONE / ERR_INVALID_STATE",
        },
        422: {"model": ErrorResponse, "description": "ERR_VALIDATION"},
        500: {"model": ErrorResponse, "description": "ERR_INTERNAL"},
    },
)
def reject_task(
    task_id: UUID,
    body: DecisionCommentInput,
    session: Session = Depends(get_db),
    user: User = Depends(_approver),
) -> DecisionResult:
    return approval_service.reject_task(session, user, task_id, body.comment)
