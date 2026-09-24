"""In-app Notification persistence for Action Engine (E4.2 / BR-29).

No delivery channels — PostgreSQL rows only, same transaction as the action.
E5.1 adds read-only listing for the current recipient.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.approval import ApprovalTask
from app.domain.enums import NotificationEventType
from app.domain.identity import User
from app.domain.notification import Notification
from app.domain.request import Request
from app.schemas.notification import NotificationListResponse, NotificationResponse

_TEXT: dict[NotificationEventType, str] = {
    NotificationEventType.REQUEST_SUBMITTED: "Новая заявка требует согласования",
    NotificationEventType.REQUEST_APPROVED: "Заявка согласована",
    NotificationEventType.REQUEST_REJECTED: "Заявка отклонена",
    NotificationEventType.REQUEST_RETURNED: "Заявка возвращена на доработку",
    NotificationEventType.REQUEST_CANCELLED: "Заявка отменена",
}

_ACTION_TO_EVENT: dict[str, NotificationEventType] = {
    "submit": NotificationEventType.REQUEST_SUBMITTED,
    "approve": NotificationEventType.REQUEST_APPROVED,
    "reject": NotificationEventType.REQUEST_REJECTED,
    "return": NotificationEventType.REQUEST_RETURNED,
    "cancel": NotificationEventType.REQUEST_CANCELLED,
}


@dataclass
class ActionOutcome:
    """Side-effect context from applying a ProcessTransition."""

    closed_task: ApprovalTask | None = None
    created_tasks: list[ApprovalTask] = field(default_factory=list)


def text_for(event_type: NotificationEventType) -> str:
    text = _TEXT.get(event_type)
    if text is None:
        raise ValueError(f"No notification text for event_type={event_type!r}")
    return text


def event_type_for_action(action_code: str) -> NotificationEventType | None:
    return _ACTION_TO_EVENT.get(action_code)


def create_notifications_for_action(
    session: Session,
    *,
    request: Request,
    action_code: str,
    outcome: ActionOutcome,
) -> list[Notification]:
    """Append Notification rows for a successful action (caller commits)."""
    event_type = event_type_for_action(action_code)
    if event_type is None:
        return []

    targets = _resolve_targets(request, action_code, outcome)
    created: list[Notification] = []
    now = datetime.now(UTC)
    for recipient_id, approval_task_id in targets:
        notification = Notification(
            recipient_id=recipient_id,
            request_id=request.id,
            approval_task_id=approval_task_id,
            event_type=event_type,
            text=text_for(event_type),
            read=False,
            created_at=now,
        )
        session.add(notification)
        created.append(notification)
    return created


def list_for_current_user(session: Session, user: User) -> NotificationListResponse:
    """Return notifications for the authenticated user only (newest first)."""
    rows = session.scalars(
        select(Notification)
        .where(Notification.recipient_id == user.id)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
    ).all()
    return NotificationListResponse(
        items=[
            NotificationResponse(
                id=row.id,
                request_id=row.request_id,
                approval_task_id=row.approval_task_id,
                event_type=row.event_type,
                text=row.text,
                read=row.read,
                created_at=row.created_at,
            )
            for row in rows
        ]
    )


def _resolve_targets(
    request: Request,
    action_code: str,
    outcome: ActionOutcome,
) -> list[tuple[uuid.UUID, int | None]]:
    """Return (recipient_id, approval_task_id) pairs."""
    if action_code == "submit":
        return [(task.assignee_user_id, task.id) for task in outcome.created_tasks]

    if action_code == "approve":
        if outcome.created_tasks:
            return [(task.assignee_user_id, task.id) for task in outcome.created_tasks]
        closed = outcome.closed_task
        return [(request.initiator_user_id, closed.id if closed is not None else None)]

    if action_code in {"reject", "return"}:
        closed = outcome.closed_task
        return [(request.initiator_user_id, closed.id if closed is not None else None)]

    if action_code == "cancel":
        return [(request.initiator_user_id, None)]

    return []
