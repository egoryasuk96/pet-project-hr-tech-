"""Request runtime: Request and working field values only (ADR-LIVE-CFG-01).

No FieldValueVersion / RouteInstance snapshots.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Identity, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.domain.approval import ApprovalTask
    from app.domain.audit import Comment, HistoryEvent
    from app.domain.catalog import RequestType
    from app.domain.identity import User
    from app.domain.notification import Notification
    from app.domain.process import Status
    from app.domain.routing import ApprovalStage


class Request(TimestampMixin, Base):
    """Employee request instance (FR-REQ-01). id = display number (ADR-ID-01)."""

    __tablename__ = "requests"

    id: Mapped[int] = mapped_column(
        Integer,
        Identity(start=10000),
        primary_key=True,
    )
    request_type_id: Mapped[int] = mapped_column(
        ForeignKey("request_types.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    initiator_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status_id: Mapped[int] = mapped_column(
        ForeignKey("statuses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    current_stage_id: Mapped[int | None] = mapped_column(
        ForeignKey("approval_stages.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    initiator: Mapped[User] = relationship(
        back_populates="initiated_requests",
        foreign_keys=[initiator_user_id],
    )
    request_type: Mapped[RequestType] = relationship(back_populates="requests")
    status: Mapped[Status] = relationship(back_populates="requests")
    current_stage: Mapped[ApprovalStage | None] = relationship(
        back_populates="requests_at_stage",
        foreign_keys=[current_stage_id],
    )
    field_values: Mapped[list[RequestFieldValue]] = relationship(back_populates="request")
    approval_tasks: Mapped[list[ApprovalTask]] = relationship(back_populates="request")
    comments: Mapped[list[Comment]] = relationship(back_populates="request")
    history_events: Mapped[list[HistoryEvent]] = relationship(back_populates="request")
    notifications: Mapped[list[Notification]] = relationship(back_populates="request")


class RequestFieldValue(Base):
    """Working values against live schema. No FK to field definition."""

    __tablename__ = "request_field_values"
    __table_args__ = (
        UniqueConstraint(
            "request_id",
            "field_code",
            name="uq_request_field_values_request_field_code",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    request_id: Mapped[int] = mapped_column(
        ForeignKey("requests.id", ondelete="RESTRICT"),
        nullable=False,
    )
    field_code: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[str | None] = mapped_column(String, nullable=True)

    request: Mapped[Request] = relationship(back_populates="field_values")
