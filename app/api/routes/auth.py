"""Authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.common import ErrorResponse
from app.services.auth_service import login as login_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate and issue a JWT access token",
    description="UC-01 / FR-AUTH-01. No refresh token. Inactive users receive FORBIDDEN.",
    responses={
        401: {"model": ErrorResponse, "description": "INVALID_CREDENTIALS"},
        403: {"model": ErrorResponse, "description": "FORBIDDEN — inactive user"},
        422: {"model": ErrorResponse, "description": "VALIDATION"},
        500: {"model": ErrorResponse, "description": "INTERNAL"},
    },
)
def login(body: LoginRequest, session: Session = Depends(get_db)) -> LoginResponse:
    return login_user(
        session,
        login_name=body.login,
        password=body.password,
        settings=get_settings(),
    )
