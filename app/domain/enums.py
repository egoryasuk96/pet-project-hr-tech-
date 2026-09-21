"""Closed domain enumerations confirmed by ERD / glossary / BR.

HistoryEvent.action is intentionally a string, not an enum (BR-24).
"""

from enum import StrEnum


class RoleCode(StrEnum):
    """Role.code — glossary / RBAC."""

    EMPLOYEE = "employee"
    APPROVER = "approver"
    ADMIN = "admin"


class RequestStatus(StrEnum):
    """Request.status — glossary / UML-SM-01."""

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


class AssignmentKind(StrEnum):
    """StageAssignment / RouteInstanceAssignment.assignment_kind — BR-12."""

    ROLE = "role"
    USER = "user"
    ROLE_AND_USER = "role_and_user"


class ApprovalTaskStatus(StrEnum):
    """ApprovalTask.status — BR-03."""

    OPEN = "open"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ApprovalDecision(StrEnum):
    """ApprovalTask.decision — FR-APP-03…05; nullable while open."""

    APPROVE = "approve"
    REJECT = "reject"
    RETURN = "return"


class CommentKind(StrEnum):
    """Comment.kind — BR-25, BR-28."""

    FREE = "free"
    DECISION = "decision"


class NotificationEventType(StrEnum):
    """Notification.event_type — documented minimum from ERD / BR-23.

    Not a complete future set: only values explicitly named in ERD.
    """

    NEW_TASK = "new_task"
    STATUS_CHANGE = "status_change"
