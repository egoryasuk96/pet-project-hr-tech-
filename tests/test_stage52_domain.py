"""Target E2 domain checks that do not require PostgreSQL."""

from sqlalchemy import Integer, UniqueConstraint, Uuid

from app.db.base import Base
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

EXPECTED_TABLES = {
    "companies",
    "departments",
    "employees",
    "users",
    "roles",
    "processes",
    "statuses",
    "actions",
    "process_transitions",
    "request_types",
    "request_field_definitions",
    "dictionaries",
    "dictionary_items",
    "approval_routes",
    "approval_stages",
    "stage_assignments",
    "requests",
    "request_field_values",
    "approval_tasks",
    "comments",
    "history_events",
    "notifications",
}

REMOVED_SNAPSHOT_TABLES = {
    "user_roles",
    "route_instances",
    "route_instance_stages",
    "route_instance_assignments",
    "field_value_versions",
}

FORBIDDEN_COLUMNS = {
    "value_version_id",
    "stage_number",
    "current_stage_number",
    "assignee_id",
    "initiator_id",
}


def test_health_endpoint_logic_without_full_app_graph() -> None:
    """Health handler is pure; full app.main may still import Pre-E2 services."""
    from app.api.routes.health import health

    assert health() == {"status": "ok"}


def test_metadata_contains_all_target_erd_tables() -> None:
    import app.domain  # noqa: F401

    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_snapshot_and_user_roles_absent_from_metadata() -> None:
    import app.domain  # noqa: F401

    present = set(Base.metadata.tables)
    assert REMOVED_SNAPSHOT_TABLES.isdisjoint(present)


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
    assert {item.value for item in FieldDataType} == {
        "text",
        "date",
        "number",
        "catalog",
        "boolean",
    }
    assert {item.value for item in AssignmentKind} == {"role", "user", "role_and_user"}
    assert {item.value for item in ApprovalTaskStatus} == {"open", "completed", "cancelled"}
    assert {item.value for item in ApprovalDecision} == {"approve", "reject", "return"}
    assert {item.value for item in CommentKind} == {"free", "decision"}
    assert {item.value for item in NotificationEventType} == {
        "new_task",
        "status_change",
        "request_submitted",
        "request_approved",
        "request_rejected",
        "request_returned",
        "request_cancelled",
    }
    assert {item.value for item in ProcessTransitionEffect} == {
        "status_only",
        "approve_advance",
    }


def test_user_pk_is_uuid_other_business_pks_are_integer() -> None:
    import app.domain  # noqa: F401

    users = Base.metadata.tables["users"]
    assert isinstance(users.c.id.type, Uuid)

    integer_pk_tables = EXPECTED_TABLES - {"users"}
    for table_name in integer_pk_tables:
        pk_col = Base.metadata.tables[table_name].c.id
        assert isinstance(pk_col.type, Integer), f"{table_name}.id must be Integer"


def test_target_request_and_approval_task_columns() -> None:
    import app.domain  # noqa: F401

    requests = Base.metadata.tables["requests"]
    approval_tasks = Base.metadata.tables["approval_tasks"]

    assert {
        "id",
        "request_type_id",
        "initiator_user_id",
        "status_id",
        "current_stage_id",
        "created_at",
        "updated_at",
    } <= set(requests.c.keys())

    assert {
        "id",
        "request_id",
        "stage_id",
        "assignee_user_id",
        "status",
        "comment",
        "completed_at",
        "created_at",
    } <= set(approval_tasks.c.keys())

    assert "decision" not in approval_tasks.c
    assert "decided_at" not in approval_tasks.c


def test_forbidden_legacy_columns_absent() -> None:
    import app.domain  # noqa: F401

    for table in Base.metadata.tables.values():
        overlap = FORBIDDEN_COLUMNS & set(table.c.keys())
        assert not overlap, f"{table.name} still has legacy columns: {overlap}"


def test_user_has_single_role_no_user_roles_table() -> None:
    import app.domain  # noqa: F401

    users = Base.metadata.tables["users"]
    assert "role_id" in users.c
    assert "employee_id" in users.c
    assert "full_name" not in users.c
    assert "user_roles" not in Base.metadata.tables


def test_request_type_has_process_id_and_code() -> None:
    import app.domain  # noqa: F401

    request_types = Base.metadata.tables["request_types"]
    assert "process_id" in request_types.c
    assert "code" in request_types.c
    assert "active" in request_types.c


def test_request_field_values_unique_and_no_definition_fk() -> None:
    import app.domain  # noqa: F401

    request_field_values = Base.metadata.tables["request_field_values"]
    assert "field_definition_id" not in request_field_values.c
    unique_cols = {
        tuple(column.name for column in constraint.columns)
        for constraint in request_field_values.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert ("request_id", "field_code") in unique_cols


def test_history_event_action_is_string() -> None:
    import app.domain  # noqa: F401

    history_events = Base.metadata.tables["history_events"]
    assert history_events.c.action.type.python_type is str
