"""Employee request lifecycle: draft, list, card, edit, submit, cancel, comments, history."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.domain.enums import RequestStatus, RoleCode
from app.domain.identity import User
from app.schemas.common import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, ErrorResponse
from app.schemas.request import (
    CancelRequestResult,
    CreateCommentInput,
    CreateRequestInput,
    CreatedComment,
    CreatedRequest,
    RequestCard,
    RequestHistory,
    RequestListItem,
    SubmitRequestResult,
    UpdateValuesInput,
    UpdatedRequestValues,
)
from app.services import request_service, submit_service

router = APIRouter(prefix="/requests", tags=["Requests"])

_employee = require_roles(RoleCode.EMPLOYEE)
_history_reader = require_roles(RoleCode.EMPLOYEE, RoleCode.APPROVER)


@router.post(
    "",
    response_model=CreatedRequest,
    status_code=status.HTTP_201_CREATED,
    summary="Create a draft request",
    description="UC-04 / FR-REQ-01. Initiator is the current user. Fields are saved later via PATCH.",
    responses={
        401: {"model": ErrorResponse, "description": "ERR_UNAUTHORIZED"},
        403: {"model": ErrorResponse, "description": "ERR_FORBIDDEN"},
        404: {"model": ErrorResponse, "description": "ERR_NOT_FOUND — request type does not exist"},
        409: {"model": ErrorResponse, "description": "ERR_INACTIVE_TYPE"},
        422: {"model": ErrorResponse, "description": "ERR_VALIDATION"},
        500: {"model": ErrorResponse, "description": "ERR_INTERNAL"},
    },
)
def create_request(
    body: CreateRequestInput,
    session: Session = Depends(get_db),
    user: User = Depends(_employee),
) -> CreatedRequest:
    return request_service.create_draft(session, user, body.request_type_id)


@router.get(
    "",
    response_model=list[RequestListItem],
    status_code=status.HTTP_200_OK,
    summary="List the current employee's requests",
    description="UC-06 / FR-CAB-02. Own requests only. Sorted by created_at descending.",
    responses={
        401: {"model": ErrorResponse, "description": "ERR_UNAUTHORIZED"},
        403: {"model": ErrorResponse, "description": "ERR_FORBIDDEN"},
        422: {"model": ErrorResponse, "description": "ERR_VALIDATION"},
        500: {"model": ErrorResponse, "description": "ERR_INTERNAL"},
    },
)
def list_requests(
    session: Session = Depends(get_db),
    user: User = Depends(_employee),
    status_filter: RequestStatus | None = Query(default=None, alias="status"),
    page: int = Query(default=DEFAULT_PAGE, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
) -> list[RequestListItem]:
    return request_service.list_own_requests(
        session,
        user,
        status=status_filter,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{request_id}",
    response_model=RequestCard,
    status_code=status.HTTP_200_OK,
    summary="Get the current employee's request card",
    description="UC-06 / FR-REQ-04. A foreign request is hidden with 404 ERR_NOT_FOUND.",
    responses={
        401: {"model": ErrorResponse, "description": "ERR_UNAUTHORIZED"},
        403: {"model": ErrorResponse, "description": "ERR_FORBIDDEN"},
        404: {"model": ErrorResponse, "description": "ERR_NOT_FOUND"},
        500: {"model": ErrorResponse, "description": "ERR_INTERNAL"},
    },
)
def get_request(
    request_id: UUID,
    session: Session = Depends(get_db),
    user: User = Depends(_employee),
) -> RequestCard:
    return request_service.get_own_request(session, user, request_id)


@router.patch(
    "/{request_id}",
    response_model=UpdatedRequestValues,
    status_code=status.HTTP_200_OK,
    summary="Save working field values",
    description="UC-04 / FR-REQ-02. Draft or returned only. Partial values allowed; required fields are checked on submit.",
    responses={
        401: {"model": ErrorResponse, "description": "ERR_UNAUTHORIZED"},
        403: {"model": ErrorResponse, "description": "ERR_FORBIDDEN"},
        404: {"model": ErrorResponse, "description": "ERR_NOT_FOUND"},
        409: {"model": ErrorResponse, "description": "ERR_INVALID_STATE"},
        422: {"model": ErrorResponse, "description": "ERR_VALIDATION"},
        500: {"model": ErrorResponse, "description": "ERR_INTERNAL"},
    },
)
def patch_request(
    request_id: UUID,
    body: UpdateValuesInput,
    session: Session = Depends(get_db),
    user: User = Depends(_employee),
) -> UpdatedRequestValues:
    return request_service.update_working_values(session, user, request_id, body.values)


@router.post(
    "/{request_id}/submit",
    response_model=SubmitRequestResult,
    status_code=status.HTTP_200_OK,
    summary="Submit a draft (or resubmit a returned request)",
    description=(
        "UC-05 / FR-REQ-03. Validates live schema and route (BR-18). "
        "Creates RouteInstance, FieldValueVersion, stage-1 tasks, and HistoryEvent."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "ERR_UNAUTHORIZED"},
        403: {"model": ErrorResponse, "description": "ERR_FORBIDDEN"},
        404: {"model": ErrorResponse, "description": "ERR_NOT_FOUND"},
        409: {
            "model": ErrorResponse,
            "description": "ERR_INVALID_STATE / ERR_INACTIVE_TYPE / ERR_ROUTE_CONFIG",
        },
        422: {"model": ErrorResponse, "description": "ERR_VALIDATION"},
        500: {"model": ErrorResponse, "description": "ERR_INTERNAL"},
    },
)
def submit_request(
    request_id: UUID,
    session: Session = Depends(get_db),
    user: User = Depends(_employee),
) -> SubmitRequestResult:
    return submit_service.submit_request(session, user, request_id)


@router.post(
    "/{request_id}/cancel",
    response_model=CancelRequestResult,
    status_code=status.HTTP_200_OK,
    summary="Cancel a request",
    description=(
        "UC-10 / FR-REQ-07 / BR-07. Cancels an own draft or returned request. "
        "Status change and HistoryEvent are atomic."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "ERR_UNAUTHORIZED"},
        403: {"model": ErrorResponse, "description": "ERR_FORBIDDEN"},
        404: {"model": ErrorResponse, "description": "ERR_NOT_FOUND"},
        409: {"model": ErrorResponse, "description": "ERR_INVALID_STATE"},
        500: {"model": ErrorResponse, "description": "ERR_INTERNAL"},
    },
)
def cancel_request(
    request_id: UUID,
    session: Session = Depends(get_db),
    user: User = Depends(_employee),
) -> CancelRequestResult:
    return request_service.cancel_request(session, user, request_id)


@router.post(
    "/{request_id}/comments",
    response_model=CreatedComment,
    status_code=status.HTTP_201_CREATED,
    summary="Add a free initiator comment",
    description=(
        "UC-06 / FR-REQ-06 / BR-28. Adds a free comment to an own request in in_approval. "
        "kind, author_id, and approval_task_id are set by the server."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "ERR_UNAUTHORIZED"},
        403: {"model": ErrorResponse, "description": "ERR_FORBIDDEN"},
        404: {"model": ErrorResponse, "description": "ERR_NOT_FOUND"},
        409: {"model": ErrorResponse, "description": "ERR_INVALID_STATE"},
        422: {"model": ErrorResponse, "description": "ERR_VALIDATION"},
        500: {"model": ErrorResponse, "description": "ERR_INTERNAL"},
    },
)
def add_comment(
    request_id: UUID,
    body: CreateCommentInput,
    session: Session = Depends(get_db),
    user: User = Depends(_employee),
) -> CreatedComment:
    return request_service.add_free_comment(session, user, request_id, body.text)


@router.get(
    "/{request_id}/history",
    response_model=RequestHistory,
    status_code=status.HTTP_200_OK,
    summary="Get request history and submitted value versions",
    description=(
        "UC-14 / FR-AUDIT-01. Chronological HistoryEvent list and FieldValueVersion snapshots. "
        "Employee: own request. Approver: request with an assigned task of any status."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "ERR_UNAUTHORIZED"},
        403: {"model": ErrorResponse, "description": "ERR_FORBIDDEN"},
        404: {"model": ErrorResponse, "description": "ERR_NOT_FOUND"},
        500: {"model": ErrorResponse, "description": "ERR_INTERNAL"},
    },
)
def get_history(
    request_id: UUID,
    session: Session = Depends(get_db),
    user: User = Depends(_history_reader),
) -> RequestHistory:
    return request_service.get_request_history(session, user, request_id)
