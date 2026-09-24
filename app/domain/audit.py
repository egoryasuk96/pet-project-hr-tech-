"""Comments and applied audit history. HistoryEvent.action is a string (BR-24)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.enums import CommentKind
from app.domain.mixins import CreatedAtMixin, IntegerPrimaryKeyMixin
from app.domain.sa_types import comment_kind_enum

if TYPE_CHECKING:
    from app.domain.approval import ApprovalTask
    from app.domain.identity import User
    from app.domain.request import Request


class Comment(IntegerPrimaryKeyMixin, CreatedAtMixin, Base):
    """Free or decision comment on a request (BR-25, BR-28)."""

    __tablename__ = "comments"

    request_id: Mapped[int] = mapped_column(
        ForeignKey("requests.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    approval_task_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("approval_tasks.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    kind: Mapped[CommentKind] = mapped_column(comment_kind_enum, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    request: Mapped[Request] = relationship(back_populates="comments")
    author: Mapped[User] = relationship(back_populates="comments")
    approval_task: Mapped[ApprovalTask | None] = relationship(back_populates="comments")


class HistoryEvent(IntegerPrimaryKeyMixin, Base):
    """Append-only applied audit. No value_version_id."""

    __tablename__ = "history_events"

    request_id: Mapped[int] = mapped_column(
        ForeignKey("requests.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(String, nullable=False)
    from_state: Mapped[str | None] = mapped_column(String, nullable=True)
    to_state: Mapped[str | None] = mapped_column(String, nullable=True)
    comment: Mapped[str | None] = mapped_column(String, nullable=True)
    at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    request: Mapped[Request] = relationship(back_populates="history_events")
    actor: Mapped[User | None] = relationship(back_populates="history_events")
