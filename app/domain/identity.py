"""Identity / RBAC models: User, Role, UserRole."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.enums import RoleCode
from app.domain.mixins import UUIDPrimaryKeyMixin
from app.domain.sa_types import role_code_enum

if TYPE_CHECKING:
    from app.domain.approval import ApprovalTask, RouteInstanceAssignment
    from app.domain.audit import Comment, HistoryEvent
    from app.domain.notification import Notification
    from app.domain.request import Request
    from app.domain.routing import StageAssignment


class User(UUIDPrimaryKeyMixin, Base):
    """User profile and credentials placeholder (password_hash — backlog auth)."""

    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("login", name="uq_users_login"),)

    login: Mapped[str] = mapped_column(String, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    position: Mapped[str | None] = mapped_column(String, nullable=True)
    department: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)

    user_roles: Mapped[list[UserRole]] = relationship(back_populates="user")
    initiated_requests: Mapped[list[Request]] = relationship(back_populates="initiator")
    stage_assignments: Mapped[list[StageAssignment]] = relationship(back_populates="user")
    route_instance_assignments: Mapped[list[RouteInstanceAssignment]] = relationship(
        back_populates="user"
    )
    assigned_tasks: Mapped[list[ApprovalTask]] = relationship(back_populates="assignee")
    comments: Mapped[list[Comment]] = relationship(back_populates="author")
    history_events: Mapped[list[HistoryEvent]] = relationship(back_populates="actor")
    notifications: Mapped[list[Notification]] = relationship(back_populates="recipient")


class Role(UUIDPrimaryKeyMixin, Base):
    """System role. code is unique (employee | approver | admin)."""

    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("code", name="uq_roles_code"),)

    code: Mapped[RoleCode] = mapped_column(role_code_enum, nullable=False)

    user_roles: Mapped[list[UserRole]] = relationship(back_populates="role")
    stage_assignments: Mapped[list[StageAssignment]] = relationship(back_populates="role")
    route_instance_assignments: Mapped[list[RouteInstanceAssignment]] = relationship(
        back_populates="role"
    )


class UserRole(Base):
    """M:N association User ↔ Role (BR-16). Composite PK."""

    __tablename__ = "user_roles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )

    user: Mapped[User] = relationship(back_populates="user_roles")
    role: Mapped[Role] = relationship(back_populates="user_roles")
