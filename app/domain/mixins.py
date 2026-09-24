"""Shared mapped-column mixins. Only timestamp fields that exist in the ERD."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Identity, Integer, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column


class UUIDPrimaryKeyMixin:
    """UUID primary key — User only (ADR-ID-01)."""

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )


class IntegerPrimaryKeyMixin:
    """Integer primary key for all non-User business entities (ADR-ID-01)."""

    id: Mapped[int] = mapped_column(
        Integer,
        Identity(),
        primary_key=True,
    )


class CreatedAtMixin:
    """created_at as a business/create timestamp (TIMESTAMPTZ)."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class TimestampMixin(CreatedAtMixin):
    """created_at + updated_at (Request only in ERD)."""

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
