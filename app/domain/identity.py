"""Identity / RBAC: User (UUID) and Role (integer). No UserRole M:N (ADR-ORG-01)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.enums import RoleCode
from app.domain.mixins import IntegerPrimaryKeyMixin, UUIDPrimaryKeyMixin
from app.domain.sa_types import role_code_enum

if TYPE_CHECKING:
    from app.domain.approval import ApprovalTask
    from app.domain.audit import Comment, HistoryEvent
    from app.domain.notification import Notification
    from app.domain.org import Employee
    from app.domain.process import ProcessTransition
    from app.domain.request import Request
    from app.domain.routing import StageAssignment


class Role(IntegerPrimaryKeyMixin, Base):
    """System role. code is unique (employee | approver | admin)."""

    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("code", name="uq_roles_code"),)

    code: Mapped[RoleCode] = mapped_column(role_code_enum, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)

    users: Mapped[list[User]] = relationship(back_populates="role")
    stage_assignments: Mapped[list[StageAssignment]] = relationship(back_populates="role")
    process_transitions: Mapped[list[ProcessTransition]] = relationship(back_populates="role")


class User(UUIDPrimaryKeyMixin, Base):
    """Account linked to Employee with a single role_id (ADR-ORG-01, ADR-ID-01)."""

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("login", name="uq_users_login"),
        UniqueConstraint("employee_id", name="uq_users_employee_id"),
    )

    login: Mapped[str] = mapped_column(String, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    role: Mapped[Role] = relationship(back_populates="users")
    employee: Mapped[Employee] = relationship(back_populates="user")
    initiated_requests: Mapped[list[Request]] = relationship(
        back_populates="initiator",
    )
    stage_assignments: Mapped[list[StageAssignment]] = relationship(back_populates="user")
    assigned_tasks: Mapped[list[ApprovalTask]] = relationship(back_populates="assignee")
    comments: Mapped[list[Comment]] = relationship(back_populates="author")
    history_events: Mapped[list[HistoryEvent]] = relationship(back_populates="actor")
    notifications: Mapped[list[Notification]] = relationship(back_populates="recipient")
