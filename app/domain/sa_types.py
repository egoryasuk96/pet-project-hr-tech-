"""Reusable SQLAlchemy PostgreSQL types for domain models."""

from enum import StrEnum

from sqlalchemy import Enum as SAEnum

from app.domain.enums import (
    ApprovalDecision,
    ApprovalTaskStatus,
    AssignmentKind,
    CommentKind,
    FieldDataType,
    NotificationEventType,
    RequestStatus,
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
request_status_enum = pg_enum(RequestStatus, "request_status")
field_data_type_enum = pg_enum(FieldDataType, "field_data_type")
assignment_kind_enum = pg_enum(AssignmentKind, "assignment_kind")
approval_task_status_enum = pg_enum(ApprovalTaskStatus, "approval_task_status")
approval_decision_enum = pg_enum(ApprovalDecision, "approval_decision")
comment_kind_enum = pg_enum(CommentKind, "comment_kind")
notification_event_type_enum = pg_enum(NotificationEventType, "notification_event_type")
