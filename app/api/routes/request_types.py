"""Active request type catalog and live form schema."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.domain.enums import RoleCode
from app.domain.identity import User
from app.schemas.common import ErrorResponse
from app.schemas.request_type import RequestTypeSchemaOut, RequestTypeSummary
from app.services import catalog_service

router = APIRouter(prefix="/request-types", tags=["RequestTypes"])

_catalog_reader = require_roles(RoleCode.EMPLOYEE, RoleCode.ADMIN)


@router.get(
    "",
    response_model=list[RequestTypeSummary],
    status_code=status.HTTP_200_OK,
    summary="List active request types",
    description="UC-03 / FR-CAT-01. Returns only active=true. Empty catalog is 200 and [].",
    responses={
        401: {"model": ErrorResponse, "description": "UNAUTHORIZED"},
        403: {"model": ErrorResponse, "description": "FORBIDDEN"},
        500: {"model": ErrorResponse, "description": "INTERNAL"},
    },
)
def list_request_types(
    session: Session = Depends(get_db),
    _: User = Depends(_catalog_reader),
) -> list[RequestTypeSummary]:
    return catalog_service.list_active_types(session)


@router.get(
    "/{type_id}",
    response_model=RequestTypeSummary,
    status_code=status.HTTP_200_OK,
    summary="Get an active request type",
    description="UC-03 / FR-CAT-02. Missing or inactive type → 404 NOT_FOUND.",
    responses={
        401: {"model": ErrorResponse, "description": "UNAUTHORIZED"},
        403: {"model": ErrorResponse, "description": "FORBIDDEN"},
        404: {"model": ErrorResponse, "description": "NOT_FOUND"},
        500: {"model": ErrorResponse, "description": "INTERNAL"},
    },
)
def get_request_type(
    type_id: int,
    session: Session = Depends(get_db),
    _: User = Depends(_catalog_reader),
) -> RequestTypeSummary:
    return catalog_service.get_active_type(session, type_id)


@router.get(
    "/{type_id}/schema",
    response_model=RequestTypeSchemaOut,
    status_code=status.HTTP_200_OK,
    summary="Get the live form schema",
    description=(
        "UC-03, UC-04 / FR-CAT-03. Fields ordered by order_no. "
        "Active dictionary items are embedded for catalog fields."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "UNAUTHORIZED"},
        403: {"model": ErrorResponse, "description": "FORBIDDEN"},
        404: {"model": ErrorResponse, "description": "NOT_FOUND"},
        500: {"model": ErrorResponse, "description": "INTERNAL"},
    },
)
def get_request_type_schema(
    type_id: int,
    session: Session = Depends(get_db),
    _: User = Depends(_catalog_reader),
) -> RequestTypeSchemaOut:
    return catalog_service.get_active_type_schema(session, type_id)
