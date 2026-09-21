"""Live approval route configuration (not RouteInstance snapshots)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.enums import AssignmentKind
from app.domain.mixins import UUIDPrimaryKeyMixin
from app.domain.sa_types import assignment_kind_enum

if TYPE_CHECKING:
    from app.domain.catalog import RequestType
    from app.domain.identity import Role, User

_ASSIGNMENT_KIND_CHECK = (
    "(assignment_kind = 'role' AND role_id IS NOT NULL AND user_id IS NULL) "
    "OR (assignment_kind = 'user' AND user_id IS NOT NULL AND role_id IS NULL) "
    "OR (assignment_kind = 'role_and_user' AND role_id IS NOT NULL AND user_id IS NOT NULL)"
)


class ApprovalRoute(UUIDPrimaryKeyMixin, Base):
    """Live route of a request type (1—0..1)."""

    __tablename__ = "approval_routes"
    __table_args__ = (
        UniqueConstraint("request_type_id", name="uq_approval_routes_request_type_id"),
    )

    request_type_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("request_types.id", ondelete="RESTRICT"),
        nullable=False,
    )

    request_type: Mapped[RequestType] = relationship(back_populates="approval_route")
    stages: Mapped[list[ApprovalStage]] = relationship(back_populates="route")


class ApprovalStage(UUIDPrimaryKeyMixin, Base):
    """Live sequential stage of an approval route (BR-02)."""

    __tablename__ = "approval_stages"
    __table_args__ = (
        UniqueConstraint("route_id", "sequence_no", name="uq_approval_stages_route_sequence"),
    )

    route_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("approval_routes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)

    route: Mapped[ApprovalRoute] = relationship(back_populates="stages")
    assignments: Mapped[list[StageAssignment]] = relationship(back_populates="stage")


class StageAssignment(UUIDPrimaryKeyMixin, Base):
    """Explicit live assignment: role and/or user (BR-12, C-13)."""

    __tablename__ = "stage_assignments"
    __table_args__ = (
        CheckConstraint(
            "role_id IS NOT NULL OR user_id IS NOT NULL",
            name="ck_stage_assignments_role_or_user",
        ),
        CheckConstraint(_ASSIGNMENT_KIND_CHECK, name="ck_stage_assignments_kind_matches_fks"),
    )

    stage_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("approval_stages.id", ondelete="RESTRICT"),
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

    stage: Mapped[ApprovalStage] = relationship(back_populates="assignments")
    role: Mapped[Role | None] = relationship(back_populates="stage_assignments")
    user: Mapped[User | None] = relationship(back_populates="stage_assignments")
