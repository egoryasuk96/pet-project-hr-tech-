"""Stage 5.2 checks that do not require PostgreSQL."""

from sqlalchemy import UniqueConstraint

from app.db import session as db_session
from app.db.base import Base
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

EXPECTED_TABLES = {
    "users",
    "roles",
    "user_roles",
    "request_types",
    "request_field_definitions",
    "dictionaries",
    "dictionary_items",
    "approval_routes",
    "approval_stages",
    "stage_assignments",
    "requests",
    "request_field_values",
    "route_instances",
    "route_instance_stages",
    "route_instance_assignments",
    "field_value_versions",
    "approval_tasks",
    "comments",
    "history_events",
    "notifications",
}


def test_app_import_does_not_connect_to_postgres() -> None:
    from app.db import session as db_session
    from app.main import app

    db_session.reset_engine()
    assert app.title
    assert db_session._engine is None


def test_health_endpoint_is_registered() -> None:
    from app.api.routes.health import health, router as health_router
    from app.main import app

    assert health() == {"status": "ok"}
    assert any(getattr(route, "path", None) == "/health" for route in health_router.routes)
    assert "/health" in app.openapi()["paths"]


def test_metadata_contains_all_erd_tables() -> None:
    import app.domain  # noqa: F401

    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_closed_enum_values() -> None:
    assert {item.value for item in RoleCode} == {"employee", "approver", "admin"}
    assert {item.value for item in RequestStatus} == {
        "draft",
        "in_approval",
        "returned",
        "approved",
        "rejected",
        "cancelled",
    }
    assert {item.value for item in FieldDataType} == {"text", "date", "number", "catalog"}
    assert {item.value for item in AssignmentKind} == {"role", "user", "role_and_user"}
    assert {item.value for item in ApprovalTaskStatus} == {"open", "completed", "cancelled"}
    assert {item.value for item in ApprovalDecision} == {"approve", "reject", "return"}
    assert {item.value for item in CommentKind} == {"free", "decision"}
    assert {item.value for item in NotificationEventType} == {"new_task", "status_change"}


def test_nullable_and_omitted_fields_match_stage52_decisions() -> None:
    import app.domain  # noqa: F401

    approval_tasks = Base.metadata.tables["approval_tasks"]
    history_events = Base.metadata.tables["history_events"]
    request_field_values = Base.metadata.tables["request_field_values"]

    assert approval_tasks.c.value_version_id.nullable is True
    assert "created_at" not in approval_tasks.c
    assert "value_version_id" not in history_events.c
    assert history_events.c.action.type.python_type is str
    assert "field_definition_id" not in request_field_values.c
    unique_cols = {
        tuple(column.name for column in constraint.columns)
        for constraint in request_field_values.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert ("request_id", "field_code") in unique_cols
