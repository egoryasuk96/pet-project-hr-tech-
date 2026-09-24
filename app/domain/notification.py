"""In-app Notification domain model (Target create + list).

Persisted on workflow Action Engine success (submit / approve / reject /
return / cancel) in the same DB transaction. List API: GET /notifications.
Mark-as-read is not implemented (Future / backlog, FR-NOTIF-03).
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Uuid, false
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.enums import NotificationEventType
from app.domain.mixins import CreatedAtMixin, IntegerPrimaryKeyMixin
from app.domain.sa_types import notification_event_type_enum

if TYPE_CHECKING:
    from app.domain.approval import ApprovalTask
    from app.domain.identity import User
    from app.domain.request import Request


class Notification(IntegerPrimaryKeyMixin, CreatedAtMixin, Base):
    """In-app notification row; create+list are Target; mark-as-read is backlog."""

    __tablename__ = "notifications"

    recipient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    request_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("requests.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    approval_task_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("approval_tasks.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    event_type: Mapped[NotificationEventType] = mapped_column(
        notification_event_type_enum,
        nullable=False,
    )
    text: Mapped[str] = mapped_column(String, nullable=False)
    read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )

    recipient: Mapped[User] = relationship(back_populates="notifications")
    request: Mapped[Request | None] = relationship(back_populates="notifications")
    approval_task: Mapped[ApprovalTask | None] = relationship(back_populates="notifications")
