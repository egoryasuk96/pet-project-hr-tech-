"""E2 E1: Target requests, request_field_values, approval_tasks.

Revision ID: 0007_e2_requests_approval_tasks
Revises: 0006_e2_catalog_live_routing
Create Date: 2026-09-23

Controlled wipe/recreate of empty Pre-E2 runtime request tables.
RequestFieldValue uses field_code (Target ERD / SQLAlchemy) — no
request_field_definition_id FK.

Temporarily drops FKs from comments / history_events / notifications onto
requests and approval_tasks; those audit tables remain UUID-shaped until E2.

Ensures minimal Status rows exist for requests.status_id FK (not a full seed).
Does NOT alter users, roles, org, process schema beyond status inserts,
catalog, or live routing.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0007_e2_requests_approval_tasks"
down_revision: Union[str, None] = "0006_e2_catalog_live_routing"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

MINIMAL_STATUSES: tuple[tuple[str, str], ...] = (
    ("draft", "Черновик"),
    ("in_approval", "На согласовании"),
    ("returned", "Возвращена"),
    ("approved", "Согласована"),
    ("rejected", "Отклонена"),
    ("cancelled", "Отменена"),
)


def _enum(name: str, values: tuple[str, ...]) -> postgresql.ENUM:
    return postgresql.ENUM(*values, name=name, create_type=False)


def _ensure_statuses(bind) -> None:
    for code, name in MINIMAL_STATUSES:
        exists = bind.execute(
            sa.text("SELECT 1 FROM statuses WHERE code = :code"),
            {"code": code},
        ).scalar()
        if exists is None:
            bind.execute(
                sa.text(
                    """
                    INSERT INTO statuses (code, name, description, active)
                    VALUES (:code, :name, NULL, true)
                    """
                ),
                {"code": code, "name": name},
            )


def upgrade() -> None:
    bind = op.get_bind()
    _ensure_statuses(bind)

    # Detach E2-pending audit/notification tables from Pre-E2 UUID runtime PKs.
    op.drop_constraint(
        "fk_comments_approval_task_id_approval_tasks",
        "comments",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_comments_request_id_requests",
        "comments",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_history_events_request_id_requests",
        "history_events",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_notifications_approval_task_id_approval_tasks",
        "notifications",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_notifications_request_id_requests",
        "notifications",
        type_="foreignkey",
    )

    op.drop_table("approval_tasks")
    op.drop_table("request_field_values")
    op.drop_table("requests")

    approval_task_status = _enum(
        "approval_task_status",
        ("open", "completed", "cancelled"),
    )
    approval_task_status.create(bind, checkfirst=True)

    op.create_table(
        "requests",
        sa.Column(
            "id",
            sa.Integer(),
            sa.Identity(start=10000),
            nullable=False,
        ),
        sa.Column("request_type_id", sa.Integer(), nullable=False),
        sa.Column("initiator_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status_id", sa.Integer(), nullable=False),
        sa.Column("current_stage_id", sa.Integer(), nullable=True),
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
            ["request_type_id"],
            ["request_types.id"],
            name="fk_requests_request_type_id_request_types",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["initiator_user_id"],
            ["users.id"],
            name="fk_requests_initiator_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["status_id"],
            ["statuses.id"],
            name="fk_requests_status_id_statuses",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["current_stage_id"],
            ["approval_stages.id"],
            name="fk_requests_current_stage_id_approval_stages",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_requests"),
    )
    op.create_index("ix_requests_request_type_id", "requests", ["request_type_id"])
    op.create_index("ix_requests_initiator_user_id", "requests", ["initiator_user_id"])
    op.create_index("ix_requests_status_id", "requests", ["status_id"])
    op.create_index("ix_requests_current_stage_id", "requests", ["current_stage_id"])

    op.create_table(
        "request_field_values",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("request_id", sa.Integer(), nullable=False),
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
        "approval_tasks",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column("stage_id", sa.Integer(), nullable=False),
        sa.Column("assignee_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", approval_task_status, nullable=False),
        sa.Column("comment", sa.String(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["request_id"],
            ["requests.id"],
            name="fk_approval_tasks_request_id_requests",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["stage_id"],
            ["approval_stages.id"],
            name="fk_approval_tasks_stage_id_approval_stages",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["assignee_user_id"],
            ["users.id"],
            name="fk_approval_tasks_assignee_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_approval_tasks"),
    )
    op.create_index("ix_approval_tasks_request_id", "approval_tasks", ["request_id"])
    op.create_index("ix_approval_tasks_stage_id", "approval_tasks", ["stage_id"])
    op.create_index(
        "ix_approval_tasks_assignee_user_id_status",
        "approval_tasks",
        ["assignee_user_id", "status"],
    )


def downgrade() -> None:
    """Restore empty Pre-E2 UUID request / field_value / approval_task shells."""
    bind = op.get_bind()
    request_status = _enum(
        "request_status",
        ("draft", "in_approval", "returned", "approved", "rejected", "cancelled"),
    )
    approval_task_status = _enum(
        "approval_task_status",
        ("open", "completed", "cancelled"),
    )
    approval_decision = _enum(
        "approval_decision",
        ("approve", "reject", "return"),
    )
    request_status.create(bind, checkfirst=True)
    approval_task_status.create(bind, checkfirst=True)
    approval_decision.create(bind, checkfirst=True)

    op.drop_table("approval_tasks")
    op.drop_table("request_field_values")
    op.drop_table("requests")

    uuid_pk = lambda: sa.Column(  # noqa: E731
        "id",
        postgresql.UUID(as_uuid=True),
        server_default=sa.text("gen_random_uuid()"),
        nullable=False,
    )

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
        "approval_tasks",
        uuid_pk(),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("stage_number", sa.Integer(), nullable=False),
        sa.Column("assignee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", approval_task_status, nullable=False),
        sa.Column("decision", approval_decision, nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
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
        sa.PrimaryKeyConstraint("id", name="pk_approval_tasks"),
    )
    op.create_index("ix_approval_tasks_request_id", "approval_tasks", ["request_id"])
    op.create_index(
        "ix_approval_tasks_assignee_id_status",
        "approval_tasks",
        ["assignee_id", "status"],
    )

    op.create_foreign_key(
        "fk_comments_request_id_requests",
        "comments",
        "requests",
        ["request_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_comments_approval_task_id_approval_tasks",
        "comments",
        "approval_tasks",
        ["approval_task_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_history_events_request_id_requests",
        "history_events",
        "requests",
        ["request_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_notifications_request_id_requests",
        "notifications",
        "requests",
        ["request_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_notifications_approval_task_id_approval_tasks",
        "notifications",
        "approval_tasks",
        ["approval_task_id"],
        ["id"],
        ondelete="RESTRICT",
    )
