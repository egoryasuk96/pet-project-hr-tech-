"""Process configuration: Process, Status, Action, ProcessTransition (ADR-ACTION-01).

No process versioning — live config only (ADR-LIVE-CFG-01).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.enums import ProcessTransitionEffect
from app.domain.mixins import IntegerPrimaryKeyMixin
from app.domain.sa_types import process_transition_effect_enum

if TYPE_CHECKING:
    from app.domain.catalog import RequestType
    from app.domain.identity import Role
    from app.domain.request import Request


class Process(IntegerPrimaryKeyMixin, Base):
    """Named process owning request types and transitions."""

    __tablename__ = "processes"
    __table_args__ = (UniqueConstraint("code", name="uq_processes_code"),)

    code: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)

    request_types: Mapped[list[RequestType]] = relationship(back_populates="process")
    transitions: Mapped[list[ProcessTransition]] = relationship(back_populates="process")


class Status(IntegerPrimaryKeyMixin, Base):
    """Request lifecycle status (Status.code matches RequestStatus values)."""

    __tablename__ = "statuses"
    __table_args__ = (UniqueConstraint("code", name="uq_statuses_code"),)

    code: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)

    requests: Mapped[list[Request]] = relationship(back_populates="status")
    transitions_from: Mapped[list[ProcessTransition]] = relationship(
        back_populates="from_status",
        foreign_keys="ProcessTransition.from_status_id",
    )
    transitions_to: Mapped[list[ProcessTransition]] = relationship(
        back_populates="to_status",
        foreign_keys="ProcessTransition.to_status_id",
    )


class Action(IntegerPrimaryKeyMixin, Base):
    """Configurable action (submit, approve, reject, return, cancel, …)."""

    __tablename__ = "actions"
    __table_args__ = (UniqueConstraint("code", name="uq_actions_code"),)

    code: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)

    transitions: Mapped[list[ProcessTransition]] = relationship(back_populates="action")


class ProcessTransition(IntegerPrimaryKeyMixin, Base):
    """Live from_status + action → to_status for a role (ADR-ACTION-01)."""

    __tablename__ = "process_transitions"

    process_id: Mapped[int] = mapped_column(
        ForeignKey("processes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    from_status_id: Mapped[int] = mapped_column(
        ForeignKey("statuses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    action_id: Mapped[int] = mapped_column(
        ForeignKey("actions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    to_status_id: Mapped[int] = mapped_column(
        ForeignKey("statuses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    effect: Mapped[ProcessTransitionEffect] = mapped_column(
        process_transition_effect_enum,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)

    process: Mapped[Process] = relationship(back_populates="transitions")
    from_status: Mapped[Status] = relationship(
        back_populates="transitions_from",
        foreign_keys=[from_status_id],
    )
    to_status: Mapped[Status] = relationship(
        back_populates="transitions_to",
        foreign_keys=[to_status_id],
    )
    action: Mapped[Action] = relationship(back_populates="transitions")
    role: Mapped[Role] = relationship(back_populates="process_transitions")
