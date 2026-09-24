"""ApprovalTask runtime against live ApprovalStage (ADR-LIVE-CFG-01).

No RouteInstance* snapshots. No value_version_id / stage_number / assignee_id.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.enums import ApprovalTaskStatus
from app.domain.mixins import CreatedAtMixin, IntegerPrimaryKeyMixin
from app.domain.sa_types import approval_task_status_enum

if TYPE_CHECKING:
    from app.domain.audit import Comment
    from app.domain.identity import User
    from app.domain.notification import Notification
    from app.domain.request import Request
    from app.domain.routing import ApprovalStage


class ApprovalTask(IntegerPrimaryKeyMixin, CreatedAtMixin, Base):
    """Approver work item on a live stage. created_at immutable (OQ-04 / C-16)."""

    __tablename__ = "approval_tasks"
    __table_args__ = (
        Index("ix_approval_tasks_assignee_user_id_status", "assignee_user_id", "status"),
    )

    request_id: Mapped[int] = mapped_column(
        ForeignKey("requests.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    stage_id: Mapped[int] = mapped_column(
        ForeignKey("approval_stages.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    assignee_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[ApprovalTaskStatus] = mapped_column(
        approval_task_status_enum,
        nullable=False,
    )
    comment: Mapped[str | None] = mapped_column(String, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    request: Mapped[Request] = relationship(back_populates="approval_tasks")
    stage: Mapped[ApprovalStage] = relationship(back_populates="approval_tasks")
    assignee: Mapped[User] = relationship(
        back_populates="assigned_tasks",
        foreign_keys=[assignee_user_id],
    )
    comments: Mapped[list[Comment]] = relationship(back_populates="approval_task")
    notifications: Mapped[list[Notification]] = relationship(back_populates="approval_task")
