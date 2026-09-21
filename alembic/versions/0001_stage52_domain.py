"""Stage 5.2 domain schema: ERD entities, constraints, PostgreSQL enums.

Revision ID: 0001_stage52_domain
Revises:
Create Date: 2026-09-21

Does not insert demo/seed data.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_stage52_domain"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ENUM_DEFINITIONS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("role_code", ("employee", "approver", "admin")),
    (
        "request_status",
        ("draft", "in_approval", "returned", "approved", "rejected", "cancelled"),
    ),
    ("field_data_type", ("text", "date", "number", "catalog")),
    ("assignment_kind", ("role", "user", "role_and_user")),
    ("approval_task_status", ("open", "completed", "cancelled")),
    ("approval_decision", ("approve", "reject", "return")),
    ("comment_kind", ("free", "decision")),
    ("notification_event_type", ("new_task", "status_change")),
)

ASSIGNMENT_KIND_CHECK = (
    "(assignment_kind = 'role' AND role_id IS NOT NULL AND user_id IS NULL) "
    "OR (assignment_kind = 'user' AND user_id IS NOT NULL AND role_id IS NULL) "
    "OR (assignment_kind = 'role_and_user' AND role_id IS NOT NULL AND user_id IS NOT NULL)"
)

TABLES_DROP_ORDER = (
    "notifications",
    "history_events",
    "comments",
    "approval_tasks",
    "field_value_versions",
    "route_instance_assignments",
    "route_instance_stages",
    "route_instances",
    "request_field_values",
    "requests",
    "stage_assignments",
    "approval_stages",
    "approval_routes",
    "request_field_definitions",
    "dictionary_items",
    "dictionaries",
    "request_types",
    "user_roles",
    "users",
    "roles",
)


def _enum(name: str, values: tuple[str, ...]) -> postgresql.ENUM:
    return postgresql.ENUM(*values, name=name, create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    for name, values in ENUM_DEFINITIONS:
        postgresql.ENUM(*values, name=name).create(bind, checkfirst=False)

    role_code = _enum("role_code", ("employee", "approver", "admin"))
    request_status = _enum(
        "request_status",
        ("draft", "in_approval", "returned", "approved", "rejected", "cancelled"),
    )
    field_data_type = _enum("field_data_type", ("text", "date", "number", "catalog"))
    assignment_kind = _enum("assignment_kind", ("role", "user", "role_and_user"))
    approval_task_status = _enum("approval_task_status", ("open", "completed", "cancelled"))
    approval_decision = _enum("approval_decision", ("approve", "reject", "return"))
    comment_kind = _enum("comment_kind", ("free", "decision"))
    notification_event_type = _enum("notification_event_type", ("new_task", "status_change"))

    uuid_pk = lambda: sa.Column(  # noqa: E731
        "id",
        postgresql.UUID(as_uuid=True),
        server_default=sa.text("gen_random_uuid()"),
        nullable=False,
    )

    op.create_table(
        "roles",
        uuid_pk(),
        sa.Column("code", role_code, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_roles"),
        sa.UniqueConstraint("code", name="uq_roles_code"),
    )

    op.create_table(
        "users",
        uuid_pk(),
        sa.Column("login", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=True),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("position", sa.String(), nullable=True),
        sa.Column("department", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("login", name="uq_users_login"),
    )

    op.create_table(
        "user_roles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_user_roles_user_id_users", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["role_id"], ["roles.id"], name="fk_user_roles_role_id_roles", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("user_id", "role_id", name="pk_user_roles"),
    )
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"])

    op.create_table(
        "dictionaries",
        uuid_pk(),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_dictionaries"),
    )

    op.create_table(
        "dictionary_items",
        uuid_pk(),
        sa.Column("dictionary_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["dictionary_id"],
            ["dictionaries.id"],
            name="fk_dictionary_items_dictionary_id_dictionaries",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_dictionary_items"),
        sa.UniqueConstraint(
            "dictionary_id", "code", name="uq_dictionary_items_dictionary_code"
        ),
    )

    op.create_table(
        "request_types",
        uuid_pk(),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_request_types"),
    )

    op.create_table(
        "request_field_definitions",
        uuid_pk(),
        sa.Column("request_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("data_type", field_data_type, nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False),
        sa.Column("order_no", sa.Integer(), nullable=False),
        sa.Column("dictionary_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.CheckConstraint(
            "dictionary_id IS NULL OR data_type = 'catalog'",
            name="ck_request_field_definitions_dictionary_catalog",
        ),
        sa.ForeignKeyConstraint(
            ["request_type_id"],
            ["request_types.id"],
            name="fk_request_field_definitions_request_type_id_request_types",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["dictionary_id"],
            ["dictionaries.id"],
            name="fk_request_field_definitions_dictionary_id_dictionaries",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_request_field_definitions"),
        sa.UniqueConstraint(
            "request_type_id", "code", name="uq_request_field_definitions_type_code"
        ),
    )
    op.create_index(
        "ix_request_field_definitions_dictionary_id",
        "request_field_definitions",
        ["dictionary_id"],
    )

    op.create_table(
        "approval_routes",
        uuid_pk(),
        sa.Column("request_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["request_type_id"],
            ["request_types.id"],
            name="fk_approval_routes_request_type_id_request_types",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_approval_routes"),
        sa.UniqueConstraint("request_type_id", name="uq_approval_routes_request_type_id"),
    )

    op.create_table(
        "approval_stages",
        uuid_pk(),
        sa.Column("route_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("sequence_no", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["route_id"],
            ["approval_routes.id"],
            name="fk_approval_stages_route_id_approval_routes",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_approval_stages"),
        sa.UniqueConstraint(
            "route_id", "sequence_no", name="uq_approval_stages_route_sequence"
        ),
    )

    op.create_table(
        "stage_assignments",
        uuid_pk(),
        sa.Column("stage_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assignment_kind", assignment_kind, nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.CheckConstraint(
            "role_id IS NOT NULL OR user_id IS NOT NULL",
            name="ck_stage_assignments_role_or_user",
        ),
        sa.CheckConstraint(ASSIGNMENT_KIND_CHECK, name="ck_stage_assignments_kind_matches_fks"),
        sa.ForeignKeyConstraint(
            ["stage_id"],
            ["approval_stages.id"],
            name="fk_stage_assignments_stage_id_approval_stages",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
            name="fk_stage_assignments_role_id_roles",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_stage_assignments_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_stage_assignments"),
    )
    op.create_index("ix_stage_assignments_stage_id", "stage_assignments", ["stage_id"])
    op.create_index("ix_stage_assignments_role_id", "stage_assignments", ["role_id"])
    op.create_index("ix_stage_assignments_user_id", "stage_assignments", ["user_id"])

    op.create_table(
        "requests",
        uuid_pk(),
        sa.Column("initiator_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", request_status, nullable=False),
        sa.Column("current_stage_number", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["initiator_id"],
            ["users.id"],
            name="fk_requests_initiator_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["request_type_id"],
            ["request_types.id"],
            name="fk_requests_request_type_id_request_types",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_requests"),
    )
    op.create_index("ix_requests_initiator_id", "requests", ["initiator_id"])
    op.create_index("ix_requests_request_type_id", "requests", ["request_type_id"])
    op.create_index("ix_requests_status", "requests", ["status"])

    op.create_table(
        "request_field_values",
        uuid_pk(),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field_code", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["request_id"],
            ["requests.id"],
            name="fk_request_field_values_request_id_requests",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_request_field_values"),
        sa.UniqueConstraint(
            "request_id",
            "field_code",
            name="uq_request_field_values_request_field_code",
        ),
    )

    op.create_table(
        "route_instances",
        uuid_pk(),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["request_id"],
            ["requests.id"],
            name="fk_route_instances_request_id_requests",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_route_instances"),
        sa.UniqueConstraint("request_id", name="uq_route_instances_request_id"),
    )

    op.create_table(
        "route_instance_stages",
        uuid_pk(),
        sa.Column("route_instance_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("sequence_no", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["route_instance_id"],
            ["route_instances.id"],
            name="fk_route_instance_stages_route_instance_id_route_instances",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_route_instance_stages"),
        sa.UniqueConstraint(
            "route_instance_id",
            "sequence_no",
            name="uq_route_instance_stages_instance_sequence",
        ),
    )

    op.create_table(
        "route_instance_assignments",
        uuid_pk(),
        sa.Column("instance_stage_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assignment_kind", assignment_kind, nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.CheckConstraint(
            "role_id IS NOT NULL OR user_id IS NOT NULL",
            name="ck_route_instance_assignments_role_or_user",
        ),
        sa.CheckConstraint(
            ASSIGNMENT_KIND_CHECK,
            name="ck_route_instance_assignments_kind_matches_fks",
        ),
        sa.ForeignKeyConstraint(
            ["instance_stage_id"],
            ["route_instance_stages.id"],
            name="fk_route_instance_assignments_instance_stage_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
            name="fk_route_instance_assignments_role_id_roles",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_route_instance_assignments_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_route_instance_assignments"),
    )
    op.create_index(
        "ix_route_instance_assignments_instance_stage_id",
        "route_instance_assignments",
        ["instance_stage_id"],
    )
    op.create_index(
        "ix_route_instance_assignments_role_id",
        "route_instance_assignments",
        ["role_id"],
    )
    op.create_index(
        "ix_route_instance_assignments_user_id",
        "route_instance_assignments",
        ["user_id"],
    )

    op.create_table(
        "field_value_versions",
        uuid_pk(),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("submit_number", sa.Integer(), nullable=False),
        sa.Column("schema_document", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("values_document", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["request_id"],
            ["requests.id"],
            name="fk_field_value_versions_request_id_requests",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_field_value_versions"),
        sa.UniqueConstraint(
            "request_id",
            "submit_number",
            name="uq_field_value_versions_request_submit_number",
        ),
    )

    op.create_table(
        "approval_tasks",
        uuid_pk(),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("stage_number", sa.Integer(), nullable=False),
        sa.Column("assignee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", approval_task_status, nullable=False),
        sa.Column("decision", approval_decision, nullable=True),
        sa.Column("value_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["request_id"],
            ["requests.id"],
            name="fk_approval_tasks_request_id_requests",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["assignee_id"],
            ["users.id"],
            name="fk_approval_tasks_assignee_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["value_version_id"],
            ["field_value_versions.id"],
            name="fk_approval_tasks_value_version_id_field_value_versions",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_approval_tasks"),
    )
    op.create_index("ix_approval_tasks_request_id", "approval_tasks", ["request_id"])
    op.create_index(
        "ix_approval_tasks_assignee_id_status",
        "approval_tasks",
        ["assignee_id", "status"],
    )
    op.create_index(
        "ix_approval_tasks_value_version_id",
        "approval_tasks",
        ["value_version_id"],
    )

    op.create_table(
        "comments",
        uuid_pk(),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("approval_task_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("kind", comment_kind, nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["request_id"],
            ["requests.id"],
            name="fk_comments_request_id_requests",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["users.id"],
            name="fk_comments_author_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["approval_task_id"],
            ["approval_tasks.id"],
            name="fk_comments_approval_task_id_approval_tasks",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_comments"),
    )
    op.create_index("ix_comments_request_id", "comments", ["request_id"])
    op.create_index("ix_comments_author_id", "comments", ["author_id"])
    op.create_index("ix_comments_approval_task_id", "comments", ["approval_task_id"])

    op.create_table(
        "history_events",
        uuid_pk(),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("from_state", sa.String(), nullable=True),
        sa.Column("to_state", sa.String(), nullable=True),
        sa.Column("comment", sa.String(), nullable=True),
        sa.Column(
            "at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["request_id"],
            ["requests.id"],
            name="fk_history_events_request_id_requests",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
            name="fk_history_events_actor_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_history_events"),
    )
    op.create_index("ix_history_events_request_id", "history_events", ["request_id"])
    op.create_index("ix_history_events_actor_id", "history_events", ["actor_id"])

    op.create_table(
        "notifications",
        uuid_pk(),
        sa.Column("recipient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approval_task_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", notification_event_type, nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("read", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["recipient_id"],
            ["users.id"],
            name="fk_notifications_recipient_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["request_id"],
            ["requests.id"],
            name="fk_notifications_request_id_requests",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["approval_task_id"],
            ["approval_tasks.id"],
            name="fk_notifications_approval_task_id_approval_tasks",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_notifications"),
    )
    op.create_index("ix_notifications_recipient_id", "notifications", ["recipient_id"])
    op.create_index("ix_notifications_request_id", "notifications", ["request_id"])
    op.create_index(
        "ix_notifications_approval_task_id",
        "notifications",
        ["approval_task_id"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    for table in TABLES_DROP_ORDER:
        op.drop_table(table)
    for name, values in reversed(ENUM_DEFINITIONS):
        postgresql.ENUM(*values, name=name).drop(bind, checkfirst=False)
