"""Domain models and closed enums (Target E2). Business services are separate."""

from app.domain.approval import ApprovalTask
from app.domain.audit import Comment, HistoryEvent
from app.domain.catalog import Dictionary, DictionaryItem, RequestFieldDefinition, RequestType
from app.domain.enums import (
    ApprovalDecision,
    ApprovalTaskStatus,
    AssignmentKind,
    CommentKind,
    FieldDataType,
    NotificationEventType,
    ProcessTransitionEffect,
    RequestStatus,
    RoleCode,
)
from app.domain.identity import Role, User
from app.domain.notification import Notification
from app.domain.org import Company, Department, Employee
from app.domain.process import Action, Process, ProcessTransition, Status
from app.domain.request import Request, RequestFieldValue
from app.domain.routing import ApprovalRoute, ApprovalStage, StageAssignment

__all__ = [
    "Action",
    "ApprovalDecision",
    "ApprovalRoute",
    "ApprovalStage",
    "ApprovalTask",
    "ApprovalTaskStatus",
    "AssignmentKind",
    "Comment",
    "CommentKind",
    "Company",
    "Department",
    "Dictionary",
    "DictionaryItem",
    "Employee",
    "FieldDataType",
    "HistoryEvent",
    "Notification",
    "NotificationEventType",
    "Process",
    "ProcessTransition",
    "ProcessTransitionEffect",
    "Request",
    "RequestFieldDefinition",
    "RequestFieldValue",
    "RequestStatus",
    "RequestType",
    "Role",
    "RoleCode",
    "StageAssignment",
    "Status",
    "User",
]
