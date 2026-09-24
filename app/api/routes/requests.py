"""Employee request lifecycle: Target read API + Legacy write wrappers."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.domain.enums import RoleCode
from app.domain.identity import User
from app.schemas.common import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, ErrorResponse
from app.schemas.history import HistoryEventListResponse
from app.schemas.request import (
    ActionExecuteInput,
    AvailableActionsResponse,
    CreateCommentInput,
    CreateRequestInput,
    CreatedComment,
    CreatedRequest,
    RequestCard,
    RequestListItem,
    UpdateValuesInput,
    UpdatedRequestValues,
)
from app.services import action_engine, available_actions_service, history_service, request_service, submit_service

router = APIRouter(prefix="/requests", tags=["Requests"])

_employee = require_roles(RoleCode.EMPLOYEE)
_request_reader = require_roles(RoleCode.EMPLOYEE, RoleCode.APPROVER)
_history_reader = require_roles(RoleCode.EMPLOYEE, RoleCode.APPROVER)
_actions_reader = require_roles(RoleCode.EMPLOYEE, RoleCode.APPROVER)
_action_executor = require_roles(RoleCode.EMPLOYEE, RoleCode.APPROVER, RoleCode.ADMIN)


@router.post(
    "",
    response_model=CreatedRequest,
    status_code=status.HTTP_201_CREATED,
    summary="Create a draft request",
    description="UC-04 / FR-REQ-01. Initiator is the current user. Fields are saved later via PATCH.",
    responses={
        401: {"model": ErrorResponse, "description": "UNAUTHORIZED"},
        403: {"model": ErrorResponse, "description": "FORBIDDEN"},
        404: {"model": ErrorResponse, "description": "NOT_FOUND — request type does not exist"},
        409: {"model": ErrorResponse, "description": "INACTIVE_TYPE"},
        422: {"model": ErrorResponse, "description": "VALIDATION"},
        500: {"model": ErrorResponse, "description": "INTERNAL"},
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
        401: {"model": ErrorResponse, "description": "UNAUTHORIZED"},
        403: {"model": ErrorResponse, "description": "FORBIDDEN"},
        422: {"model": ErrorResponse, "description": "VALIDATION"},
        500: {"model": ErrorResponse, "description": "INTERNAL"},
    },
)
def list_requests(
    session: Session = Depends(get_db),
    user: User = Depends(_employee),
    status_filter: str | None = Query(default=None, alias="status"),
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
    "/{request_id}/available-actions",
    response_model=AvailableActionsResponse,
    status_code=status.HTTP_200_OK,
    summary="List available actions for a request (read-only)",
    description=(
        "E3.1 / ADR-ACTION-01. Computes actions from live ProcessTransition "
        "for the current request status and user role. Does not execute transitions."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "UNAUTHORIZED"},
        403: {"model": ErrorResponse, "description": "FORBIDDEN"},
        404: {"model": ErrorResponse, "description": "NOT_FOUND"},
        500: {"model": ErrorResponse, "description": "INTERNAL"},
    },
)
def get_available_actions(
    request_id: int,
    session: Session = Depends(get_db),
    user: User = Depends(_actions_reader),
) -> AvailableActionsResponse:
    return available_actions_service.list_available_actions(session, user, request_id)


@router.post(
    "/{request_id}/actions/{action_id}",
    response_model=RequestCard,
    status_code=status.HTTP_200_OK,
    summary="Execute a configured action on a request",
    description=(
        "E3.2 / ADR-ACTION-01. Single Target execute endpoint. "
        "Permission and target status come from live ProcessTransition."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "UNAUTHORIZED"},
        403: {"model": ErrorResponse, "description": "FORBIDDEN_APPROVAL"},
        404: {"model": ErrorResponse, "description": "NOT_FOUND"},
        409: {"model": ErrorResponse, "description": "REQUEST_ACTION_NOT_ALLOWED / ROUTE_CONFIG"},
        422: {"model": ErrorResponse, "description": "VALIDATION"},
        500: {"model": ErrorResponse, "description": "INTERNAL"},
    },
)
def execute_request_action(
    request_id: int,
    action_id: int,
    session: Session = Depends(get_db),
    user: User = Depends(_action_executor),
    body: ActionExecuteInput = Body(default_factory=ActionExecuteInput),
) -> RequestCard:
    return action_engine.execute_action(
        session,
        user,
        request_id,
        action_id,
        comment=body.comment,
    )


@router.get(
    "/{request_id}",
    response_model=RequestCard,
    status_code=status.HTTP_200_OK,
    summary="Get a visible request card",
    description=(
        "UC-06 / UC-07 / FR-REQ-04. Employee: own request. "
        "Approver: request with own ApprovalTask (BR-14). "
        "Invisible requests return 404 NOT_FOUND."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "UNAUTHORIZED"},
        403: {"model": ErrorResponse, "description": "FORBIDDEN"},
        404: {"model": ErrorResponse, "description": "NOT_FOUND"},
        500: {"model": ErrorResponse, "description": "INTERNAL"},
    },
)
def get_request(
    request_id: int,
    session: Session = Depends(get_db),
    user: User = Depends(_request_reader),
) -> RequestCard:
    return request_service.get_visible_request_card(session, user, request_id)


@router.patch(
    "/{request_id}",
    response_model=UpdatedRequestValues,
    status_code=status.HTTP_200_OK,
    summary="Save working field values",
    description="UC-04 / FR-REQ-02. Deferred until later API stage.",
    responses={
        401: {"model": ErrorResponse, "description": "UNAUTHORIZED"},
        403: {"model": ErrorResponse, "description": "FORBIDDEN"},
        404: {"model": ErrorResponse, "description": "NOT_FOUND"},
        409: {"model": ErrorResponse, "description": "INVALID_STATE"},
        422: {"model": ErrorResponse, "description": "VALIDATION"},
        500: {"model": ErrorResponse, "description": "INTERNAL"},
    },
)
def patch_request(
    request_id: int,
    body: UpdateValuesInput,
    session: Session = Depends(get_db),
    user: User = Depends(_employee),
) -> UpdatedRequestValues:
    return request_service.update_working_values(session, user, request_id, body.values)


@router.post(
    "/{request_id}/submit",
    response_model=RequestCard,
    status_code=status.HTTP_200_OK,
    summary="Submit a draft (Legacy thin alias)",
    description="Legacy wrapper around POST .../actions/{submit_action_id}.",
    deprecated=True,
    responses={
        401: {"model": ErrorResponse, "description": "UNAUTHORIZED"},
        403: {"model": ErrorResponse, "description": "FORBIDDEN"},
        404: {"model": ErrorResponse, "description": "NOT_FOUND"},
        409: {"model": ErrorResponse, "description": "REQUEST_ACTION_NOT_ALLOWED"},
        500: {"model": ErrorResponse, "description": "INTERNAL"},
    },
)
def submit_request(
    request_id: int,
    session: Session = Depends(get_db),
    user: User = Depends(_employee),
) -> RequestCard:
    return submit_service.submit_request(session, user, request_id)


@router.post(
    "/{request_id}/cancel",
    response_model=RequestCard,
    status_code=status.HTTP_200_OK,
    summary="Cancel a request (Legacy thin alias)",
    description="Legacy wrapper around POST .../actions/{cancel_action_id}.",
    deprecated=True,
    responses={
        401: {"model": ErrorResponse, "description": "UNAUTHORIZED"},
        403: {"model": ErrorResponse, "description": "FORBIDDEN"},
        404: {"model": ErrorResponse, "description": "NOT_FOUND"},
        409: {"model": ErrorResponse, "description": "REQUEST_ACTION_NOT_ALLOWED"},
        500: {"model": ErrorResponse, "description": "INTERNAL"},
    },
)
def cancel_request(
    request_id: int,
    session: Session = Depends(get_db),
    user: User = Depends(_employee),
) -> RequestCard:
    return request_service.cancel_request(session, user, request_id)


@router.post(
    "/{request_id}/comments",
    response_model=CreatedComment,
    status_code=status.HTTP_201_CREATED,
    summary="Add a free initiator comment",
    description="Deferred until later API stage.",
    responses={
        401: {"model": ErrorResponse, "description": "UNAUTHORIZED"},
        403: {"model": ErrorResponse, "description": "FORBIDDEN"},
        404: {"model": ErrorResponse, "description": "NOT_FOUND"},
        409: {"model": ErrorResponse, "description": "INVALID_STATE"},
        422: {"model": ErrorResponse, "description": "VALIDATION"},
        500: {"model": ErrorResponse, "description": "INTERNAL"},
    },
)
def add_comment(
    request_id: int,
    body: CreateCommentInput,
    session: Session = Depends(get_db),
    user: User = Depends(_employee),
) -> CreatedComment:
    return request_service.add_free_comment(session, user, request_id, body.text)


@router.get(
    "/{request_id}/history",
    response_model=HistoryEventListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get request history",
    description=(
        "E5.1 / UC-14 / FR-AUDIT-01. Returns HistoryEvent rows for a visible request, "
        "sorted by at descending. Employee: own requests. Approver: requests with own task."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "UNAUTHORIZED"},
        403: {"model": ErrorResponse, "description": "FORBIDDEN"},
        404: {"model": ErrorResponse, "description": "NOT_FOUND"},
        500: {"model": ErrorResponse, "description": "INTERNAL"},
    },
)
def get_history(
    request_id: int,
    session: Session = Depends(get_db),
    user: User = Depends(_history_reader),
) -> HistoryEventListResponse:
    return history_service.list_request_history(session, user, request_id)
