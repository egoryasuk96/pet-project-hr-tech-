"""Domain models and closed enums (Stage 5.2). Business services are later stages."""

from app.domain.approval import (
    ApprovalTask,
    RouteInstance,
    RouteInstanceAssignment,
    RouteInstanceStage,
)
from app.domain.audit import Comment, HistoryEvent
from app.domain.catalog import Dictionary, DictionaryItem, RequestFieldDefinition, RequestType
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
from app.domain.identity import Role, User, UserRole
from app.domain.notification import Notification
from app.domain.request import FieldValueVersion, Request, RequestFieldValue
from app.domain.routing import ApprovalRoute, ApprovalStage, StageAssignment

__all__ = [
    "ApprovalDecision",
    "ApprovalRoute",
    "ApprovalStage",
    "ApprovalTask",
    "ApprovalTaskStatus",
    "AssignmentKind",
    "Comment",
    "CommentKind",
    "Dictionary",
    "DictionaryItem",
    "FieldDataType",
    "FieldValueVersion",
    "HistoryEvent",
    "Notification",
    "NotificationEventType",
    "Request",
    "RequestFieldDefinition",
    "RequestFieldValue",
    "RequestStatus",
    "RequestType",
    "Role",
    "RoleCode",
    "RouteInstance",
    "RouteInstanceAssignment",
    "RouteInstanceStage",
    "StageAssignment",
    "User",
    "UserRole",
]
