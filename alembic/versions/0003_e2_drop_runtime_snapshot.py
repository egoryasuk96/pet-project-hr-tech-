"""E2 A: wipe runtime data and drop snapshot tables.

Revision ID: 0003_e2_drop_runtime_snapshot
Revises: 0002_approval_task_created_at
Create Date: 2026-09-23

- Wipes runtime rows (tables kept for later E2 steps):
  notifications, history_events, comments, approval_tasks,
  request_field_values, requests.
- Drops snapshot tables:
  route_instance_assignments, route_instance_stages, route_instances,
  field_value_versions.
- Does NOT touch users, roles, user_roles, catalog, or live routing.
- Does NOT drop PG enums: approval_decision / request_status /
  approval_task_status / assignment_kind remain in use by kept tables.
- Does NOT seed data.

Downgrade recreates empty snapshot tables (runtime wipe is not restored).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003_e2_drop_runtime_snapshot"
down_revision: Union[str, None] = "0002_approval_task_created_at"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ASSIGNMENT_KIND_CHECK = (
    "(assignment_kind = 'role' AND role_id IS NOT NULL AND user_id IS NULL) "
    "OR (assignment_kind = 'user' AND user_id IS NOT NULL AND role_id IS NULL) "
    "OR (assignment_kind = 'role_and_user' AND role_id IS NOT NULL AND user_id IS NOT NULL)"
)

RUNTIME_TRUNCATE_ORDER = (
    "notifications",
    "history_events",
    "comments",
    "approval_tasks",
    "request_field_values",
    "requests",
)

SNAPSHOT_DROP_ORDER = (
    "route_instance_assignments",
    "route_instance_stages",
    "route_instances",
    "field_value_versions",
)


def _enum(name: str, values: tuple[str, ...]) -> postgresql.ENUM:
    return postgresql.ENUM(*values, name=name, create_type=False)


def upgrade() -> None:
    # Wipe runtime first so FK RESTRICT on snapshot/runtime graph is clear.
    # TRUNCATE ... CASCADE is unnecessary: child runtime tables are listed first.
    for table in RUNTIME_TRUNCATE_ORDER:
        op.execute(sa.text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))

    # Drop FK from approval_tasks → field_value_versions before dropping versions.
    op.drop_constraint(
        "fk_approval_tasks_value_version_id_field_value_versions",
        "approval_tasks",
        type_="foreignkey",
    )
    op.drop_index("ix_approval_tasks_value_version_id", table_name="approval_tasks")
    op.drop_column("approval_tasks", "value_version_id")

    for table in SNAPSHOT_DROP_ORDER:
        op.drop_table(table)


def downgrade() -> None:
    """Recreate empty snapshot tables and restore value_version_id column."""
    bind = op.get_bind()
    assignment_kind = _enum("assignment_kind", ("role", "user", "role_and_user"))
    # Ensure enum type is bound for create_table (already exists in DB).
    assignment_kind.create(bind, checkfirst=True)

    uuid_pk = lambda: sa.Column(  # noqa: E731
        "id",
        postgresql.UUID(as_uuid=True),
        server_default=sa.text("gen_random_uuid()"),
        nullable=False,
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

    op.add_column(
        "approval_tasks",
        sa.Column("value_version_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "ix_approval_tasks_value_version_id",
        "approval_tasks",
        ["value_version_id"],
    )
    op.create_foreign_key(
        "fk_approval_tasks_value_version_id_field_value_versions",
        "approval_tasks",
        "field_value_versions",
        ["value_version_id"],
        ["id"],
        ondelete="RESTRICT",
    )
