"""Legacy approval endpoints stub — Target execution is Action Engine (next stage)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.domain.identity import User
from app.schemas.approval import (
    ApprovalTaskCardResponse,
    ApprovalTaskListItem,
    DecisionResult,
)


def list_open_tasks(
    session: Session,
    user: User,
    *,
    page: int,
    page_size: int,
) -> list[ApprovalTaskListItem]:
    raise AppError(
        "INVALID_STATE",
        "Очередь согласования будет доступна после следующего этапа API",
        409,
    )


def get_task_card(
    session: Session,
    user: User,
    task_id: int,
) -> ApprovalTaskCardResponse:
    raise AppError(
        "INVALID_STATE",
        "Карточка задачи будет доступна после следующего этапа API",
        409,
    )


def approve_task(
    session: Session,
    user: User,
    task_id: int,
    comment: str | None,
) -> DecisionResult:
    raise AppError(
        "INVALID_STATE",
        "Approve через Legacy endpoint отключён; используйте POST /requests/{id}/actions/{action_id}",
        409,
    )


def return_task(
    session: Session,
    user: User,
    task_id: int,
    comment: str | None,
) -> DecisionResult:
    raise AppError(
        "INVALID_STATE",
        "Return через Legacy endpoint отключён; используйте POST /requests/{id}/actions/{action_id}",
        409,
    )


def reject_task(
    session: Session,
    user: User,
    task_id: int,
    comment: str | None,
) -> DecisionResult:
    raise AppError(
        "INVALID_STATE",
        "Reject через Legacy endpoint отключён; используйте POST /requests/{id}/actions/{action_id}",
        409,
    )
