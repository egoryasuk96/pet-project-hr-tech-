"""Approval task endpoints — disabled compatibility stubs (not Target-active).

Target approver flow: GET /requests/{id} → available-actions → POST .../actions/{id}.
These routes remain for compatibility and always raise INVALID_STATE (409).
"""

from __future__ import annotations

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

_STUB_NOTE = (
    "Disabled compatibility stub — not Target-active. "
    "Always returns 409 INVALID_STATE. "
    "Use GET /requests/{id}/available-actions and "
    "POST /requests/{id}/actions/{action_id} instead."
)


@router.get(
    "",
    response_model=list[ApprovalTaskListItem],
    status_code=status.HTTP_200_OK,
    deprecated=True,
    summary="[Disabled stub] List approval tasks",
    description=_STUB_NOTE,
    responses={
        401: {"model": ErrorResponse, "description": "UNAUTHORIZED"},
        403: {"model": ErrorResponse, "description": "FORBIDDEN"},
        409: {"model": ErrorResponse, "description": "INVALID_STATE — disabled stub"},
        422: {"model": ErrorResponse, "description": "VALIDATION"},
        500: {"model": ErrorResponse, "description": "INTERNAL"},
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
    deprecated=True,
    summary="[Disabled stub] Get an approval task and request card",
    description=_STUB_NOTE,
    responses={
        401: {"model": ErrorResponse, "description": "UNAUTHORIZED"},
        403: {"model": ErrorResponse, "description": "FORBIDDEN / FORBIDDEN_APPROVAL"},
        409: {"model": ErrorResponse, "description": "INVALID_STATE — disabled stub"},
        422: {"model": ErrorResponse, "description": "VALIDATION"},
        500: {"model": ErrorResponse, "description": "INTERNAL"},
    },
)
def get_approval_task(
    task_id: int,
    session: Session = Depends(get_db),
    user: User = Depends(_approver),
) -> ApprovalTaskCardResponse:
    return approval_service.get_task_card(session, user, task_id)


@router.post(
    "/{task_id}/approve",
    response_model=DecisionResult,
    status_code=status.HTTP_200_OK,
    deprecated=True,
    summary="[Disabled stub] Approve request",
    description=_STUB_NOTE,
    responses={
        401: {"model": ErrorResponse, "description": "UNAUTHORIZED"},
        403: {"model": ErrorResponse, "description": "FORBIDDEN / FORBIDDEN_APPROVAL"},
        409: {"model": ErrorResponse, "description": "INVALID_STATE — disabled stub"},
        422: {"model": ErrorResponse, "description": "VALIDATION"},
        500: {"model": ErrorResponse, "description": "INTERNAL"},
    },
)
def approve_task(
    task_id: int,
    body: DecisionCommentInput,
    session: Session = Depends(get_db),
    user: User = Depends(_approver),
) -> DecisionResult:
    return approval_service.approve_task(session, user, task_id, body.comment)


@router.post(
    "/{task_id}/return",
    response_model=DecisionResult,
    status_code=status.HTTP_200_OK,
    deprecated=True,
    summary="[Disabled stub] Return request for revision",
    description=_STUB_NOTE,
    responses={
        401: {"model": ErrorResponse, "description": "UNAUTHORIZED"},
        403: {"model": ErrorResponse, "description": "FORBIDDEN / FORBIDDEN_APPROVAL"},
        409: {"model": ErrorResponse, "description": "INVALID_STATE — disabled stub"},
        422: {"model": ErrorResponse, "description": "VALIDATION"},
        500: {"model": ErrorResponse, "description": "INTERNAL"},
    },
)
def return_task(
    task_id: int,
    body: DecisionCommentInput,
    session: Session = Depends(get_db),
    user: User = Depends(_approver),
) -> DecisionResult:
    return approval_service.return_task(session, user, task_id, body.comment)


@router.post(
    "/{task_id}/reject",
    response_model=DecisionResult,
    status_code=status.HTTP_200_OK,
    deprecated=True,
    summary="[Disabled stub] Reject request",
    description=_STUB_NOTE,
    responses={
        401: {"model": ErrorResponse, "description": "UNAUTHORIZED"},
        403: {"model": ErrorResponse, "description": "FORBIDDEN / FORBIDDEN_APPROVAL"},
        409: {"model": ErrorResponse, "description": "INVALID_STATE — disabled stub"},
        422: {"model": ErrorResponse, "description": "VALIDATION"},
        500: {"model": ErrorResponse, "description": "INTERNAL"},
    },
)
def reject_task(
    task_id: int,
    body: DecisionCommentInput,
    session: Session = Depends(get_db),
    user: User = Depends(_approver),
) -> DecisionResult:
    return approval_service.reject_task(session, user, task_id, body.comment)
