"""Reusable SQLAlchemy PostgreSQL types for domain models."""

from enum import StrEnum

from sqlalchemy import Enum as SAEnum

from app.domain.enums import (
    ApprovalTaskStatus,
    AssignmentKind,
    CommentKind,
    FieldDataType,
    NotificationEventType,
    ProcessTransitionEffect,
    RoleCode,
)


def pg_enum(enum_cls: type[StrEnum], name: str) -> SAEnum:
    """Native PostgreSQL ENUM bound to a closed StrEnum."""
    return SAEnum(
        enum_cls,
        name=name,
        native_enum=True,
        create_constraint=False,
        values_callable=lambda cls: [member.value for member in cls],
        validate_strings=True,
    )


role_code_enum = pg_enum(RoleCode, "role_code")
field_data_type_enum = pg_enum(FieldDataType, "field_data_type")
assignment_kind_enum = pg_enum(AssignmentKind, "assignment_kind")
approval_task_status_enum = pg_enum(ApprovalTaskStatus, "approval_task_status")
comment_kind_enum = pg_enum(CommentKind, "comment_kind")
notification_event_type_enum = pg_enum(NotificationEventType, "notification_event_type")
process_transition_effect_enum = pg_enum(ProcessTransitionEffect, "process_transition_effect")
