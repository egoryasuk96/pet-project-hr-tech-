"""Closed domain enumerations confirmed by ERD / glossary / BR.

HistoryEvent.action is intentionally a string, not an enum (BR-24).
Status / Action codes live in Status and Action tables; RequestStatus
remains as the closed set of Status.code values for validation helpers.
"""

from enum import StrEnum


class RoleCode(StrEnum):
    """Role.code — glossary / RBAC."""

    EMPLOYEE = "employee"
    APPROVER = "approver"
    ADMIN = "admin"


class RequestStatus(StrEnum):
    """Canonical Status.code values — glossary / UML-SM-01."""

    DRAFT = "draft"
    IN_APPROVAL = "in_approval"
    RETURNED = "returned"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class FieldDataType(StrEnum):
    """RequestFieldDefinition.data_type — glossary / ERD."""

    TEXT = "text"
    DATE = "date"
    NUMBER = "number"
    CATALOG = "catalog"
    BOOLEAN = "boolean"


class AssignmentKind(StrEnum):
    """StageAssignment.assignment_kind — BR-12."""

    ROLE = "role"
    USER = "user"
    ROLE_AND_USER = "role_and_user"


class ApprovalTaskStatus(StrEnum):
    """ApprovalTask.status — BR-03."""

    OPEN = "open"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ApprovalDecision(StrEnum):
    """Legacy Pre-E2 decision codes still used by API schemas until action engine.

    Not a column on Target ApprovalTask (comment + ProcessTransition replace it).
    """

    APPROVE = "approve"
    REJECT = "reject"
    RETURN = "return"


class CommentKind(StrEnum):
    """Comment.kind — BR-25, BR-28."""

    FREE = "free"
    DECISION = "decision"


class NotificationEventType(StrEnum):
    """Notification.event_type — closed PG enum notification_event_type.

    Legacy / generic: new_task, status_change.
    Target Action Engine (E4.2): request_* values.
    """

    NEW_TASK = "new_task"
    STATUS_CHANGE = "status_change"
    REQUEST_SUBMITTED = "request_submitted"
    REQUEST_APPROVED = "request_approved"
    REQUEST_REJECTED = "request_rejected"
    REQUEST_RETURNED = "request_returned"
    REQUEST_CANCELLED = "request_cancelled"


class ProcessTransitionEffect(StrEnum):
    """ProcessTransition.effect — ADR-ACTION-01."""

    STATUS_ONLY = "status_only"
    APPROVE_ADVANCE = "approve_advance"
