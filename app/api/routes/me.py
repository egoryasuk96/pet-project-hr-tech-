"""Current authenticated user."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user
from app.domain.identity import User
from app.schemas.auth import CurrentUser
from app.schemas.common import ErrorResponse
from app.services.auth_service import to_current_user

router = APIRouter(tags=["Current user"])


@router.get(
    "/me",
    response_model=CurrentUser,
    status_code=status.HTTP_200_OK,
    summary="Get the current user and roles",
    description="FR-AUTH-02. Requires a valid JWT. Never returns password_hash.",
    responses={
        401: {"model": ErrorResponse, "description": "ERR_UNAUTHORIZED"},
        500: {"model": ErrorResponse, "description": "ERR_INTERNAL"},
    },
)
def read_me(user: User = Depends(get_current_user)) -> CurrentUser:
    return to_current_user(user)
