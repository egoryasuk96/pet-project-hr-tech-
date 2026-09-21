"""Request runtime: Request, working field values, FieldValueVersion snapshots."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.enums import RequestStatus
from app.domain.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.domain.sa_types import request_status_enum

if TYPE_CHECKING:
    from app.domain.approval import ApprovalTask, RouteInstance
    from app.domain.audit import Comment, HistoryEvent
    from app.domain.catalog import RequestType
    from app.domain.identity import User
    from app.domain.notification import Notification


class Request(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Employee request instance (FR-REQ-01)."""

    __tablename__ = "requests"
    __table_args__ = (Index("ix_requests_status", "status"),)

    initiator_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    request_type_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("request_types.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[RequestStatus] = mapped_column(request_status_enum, nullable=False)
    current_stage_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    initiator: Mapped[User] = relationship(back_populates="initiated_requests")
    request_type: Mapped[RequestType] = relationship(back_populates="requests")
    field_values: Mapped[list[RequestFieldValue]] = relationship(back_populates="request")
    field_value_versions: Mapped[list[FieldValueVersion]] = relationship(
        back_populates="request"
    )
    route_instance: Mapped[RouteInstance | None] = relationship(
        back_populates="request",
        uselist=False,
    )
    approval_tasks: Mapped[list[ApprovalTask]] = relationship(back_populates="request")
    comments: Mapped[list[Comment]] = relationship(back_populates="request")
    history_events: Mapped[list[HistoryEvent]] = relationship(back_populates="request")
    notifications: Mapped[list[Notification]] = relationship(back_populates="request")


class RequestFieldValue(UUIDPrimaryKeyMixin, Base):
    """Working values (live schema in draft/returned). No FK to field definition."""

    __tablename__ = "request_field_values"
    __table_args__ = (
        UniqueConstraint(
            "request_id",
            "field_code",
            name="uq_request_field_values_request_field_code",
        ),
    )

    request_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("requests.id", ondelete="RESTRICT"),
        nullable=False,
    )
    field_code: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[str | None] = mapped_column(String, nullable=True)

    request: Mapped[Request] = relationship(back_populates="field_values")


class FieldValueVersion(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Append-only schema+values snapshot per successful submit (BR-26)."""

    __tablename__ = "field_value_versions"
    __table_args__ = (
        UniqueConstraint(
            "request_id",
            "submit_number",
            name="uq_field_value_versions_request_submit_number",
        ),
    )

    request_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("requests.id", ondelete="RESTRICT"),
        nullable=False,
    )
    submit_number: Mapped[int] = mapped_column(Integer, nullable=False)
    schema_document: Mapped[dict] = mapped_column(JSONB, nullable=False)
    values_document: Mapped[dict] = mapped_column(JSONB, nullable=False)

    request: Mapped[Request] = relationship(back_populates="field_value_versions")
    approval_tasks: Mapped[list[ApprovalTask]] = relationship(
        back_populates="value_version"
    )
