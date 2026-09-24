"""Current-user notifications (read-only, E5.1)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.domain.enums import RoleCode
from app.domain.identity import User
from app.schemas.common import ErrorResponse
from app.schemas.notification import NotificationListResponse
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])

_reader = require_roles(RoleCode.EMPLOYEE, RoleCode.APPROVER, RoleCode.ADMIN)


@router.get(
    "",
    response_model=NotificationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List notifications for the current user",
    description=(
        "E5.1 / UC-13. Returns only notifications where recipient_id is the "
        "authenticated user. Sorted by created_at descending."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "UNAUTHORIZED"},
        403: {"model": ErrorResponse, "description": "FORBIDDEN"},
        500: {"model": ErrorResponse, "description": "INTERNAL"},
    },
)
def list_notifications(
    session: Session = Depends(get_db),
    user: User = Depends(_reader),
) -> NotificationListResponse:
    return notification_service.list_for_current_user(session, user)
