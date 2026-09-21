"""RouteInstance snapshots and ApprovalTask runtime."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.enums import ApprovalDecision, ApprovalTaskStatus, AssignmentKind
from app.domain.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin
from app.domain.sa_types import (
    approval_decision_enum,
    approval_task_status_enum,
    assignment_kind_enum,
)

if TYPE_CHECKING:
    from app.domain.audit import Comment
    from app.domain.identity import Role, User
    from app.domain.notification import Notification
    from app.domain.request import FieldValueVersion, Request

_ASSIGNMENT_KIND_CHECK = (
    "(assignment_kind = 'role' AND role_id IS NOT NULL AND user_id IS NULL) "
    "OR (assignment_kind = 'user' AND user_id IS NOT NULL AND role_id IS NULL) "
    "OR (assignment_kind = 'role_and_user' AND role_id IS NOT NULL AND user_id IS NOT NULL)"
)


class RouteInstance(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Write-once route copy created on first successful submit (BR-08)."""

    __tablename__ = "route_instances"
    __table_args__ = (
        UniqueConstraint("request_id", name="uq_route_instances_request_id"),
    )

    request_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("requests.id", ondelete="RESTRICT"),
        nullable=False,
    )

    request: Mapped[Request] = relationship(back_populates="route_instance")
    stages: Mapped[list[RouteInstanceStage]] = relationship(back_populates="route_instance")


class RouteInstanceStage(UUIDPrimaryKeyMixin, Base):
    """Frozen stage of a RouteInstance (sequence unique per instance)."""

    __tablename__ = "route_instance_stages"
    __table_args__ = (
        UniqueConstraint(
            "route_instance_id",
            "sequence_no",
            name="uq_route_instance_stages_instance_sequence",
        ),
    )

    route_instance_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("route_instances.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)

    route_instance: Mapped[RouteInstance] = relationship(back_populates="stages")
    assignments: Mapped[list[RouteInstanceAssignment]] = relationship(
        back_populates="instance_stage"
    )


class RouteInstanceAssignment(UUIDPrimaryKeyMixin, Base):
    """Frozen assignment copied at first submit (not live StageAssignment)."""

    __tablename__ = "route_instance_assignments"
    __table_args__ = (
        CheckConstraint(
            "role_id IS NOT NULL OR user_id IS NOT NULL",
            name="ck_route_instance_assignments_role_or_user",
        ),
        CheckConstraint(
            _ASSIGNMENT_KIND_CHECK,
            name="ck_route_instance_assignments_kind_matches_fks",
        ),
    )

    instance_stage_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "route_instance_stages.id",
            ondelete="RESTRICT",
            name="fk_route_instance_assignments_instance_stage_id",
        ),
        nullable=False,
        index=True,
    )
    assignment_kind: Mapped[AssignmentKind] = mapped_column(
        assignment_kind_enum,
        nullable=False,
    )
    role_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    instance_stage: Mapped[RouteInstanceStage] = relationship(back_populates="assignments")
    role: Mapped[Role | None] = relationship(back_populates="route_instance_assignments")
    user: Mapped[User | None] = relationship(back_populates="route_instance_assignments")


class ApprovalTask(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Approver work item. created_at immutable (OQ-04 / C-16). value_version_id nullable (RR-FK-01)."""

    __tablename__ = "approval_tasks"
    __table_args__ = (
        Index("ix_approval_tasks_assignee_id_status", "assignee_id", "status"),
    )

    request_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("requests.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    stage_number: Mapped[int] = mapped_column(Integer, nullable=False)
    assignee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[ApprovalTaskStatus] = mapped_column(
        approval_task_status_enum,
        nullable=False,
    )
    decision: Mapped[ApprovalDecision | None] = mapped_column(
        approval_decision_enum,
        nullable=True,
    )
    value_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("field_value_versions.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    request: Mapped[Request] = relationship(back_populates="approval_tasks")
    assignee: Mapped[User] = relationship(back_populates="assigned_tasks")
    value_version: Mapped[FieldValueVersion | None] = relationship(
        back_populates="approval_tasks"
    )
    comments: Mapped[list[Comment]] = relationship(back_populates="approval_task")
    notifications: Mapped[list[Notification]] = relationship(back_populates="approval_task")
