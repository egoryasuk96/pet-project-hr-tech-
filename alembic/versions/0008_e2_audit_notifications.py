"""E2 E2: Target comments, history_events, notifications (Integer PK).

Revision ID: 0008_e2_audit_notifications
Revises: 0007_e2_requests_approval_tasks
Create Date: 2026-09-23

Controlled wipe/recreate of empty Pre-E2 audit/notification tables.
Restores FKs to Target Integer requests / approval_tasks and UUID users.
Does NOT alter users, catalog, routing, org/process, or request runtime tables.

Note: revision id kept <= 32 chars (alembic_version.version_num).
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0008_e2_audit_notifications"
down_revision: Union[str, None] = "0007_e2_requests_approval_tasks"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _enum(name: str, values: tuple[str, ...]) -> postgresql.ENUM:
    return postgresql.ENUM(*values, name=name, create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    comment_kind = _enum("comment_kind", ("free", "decision"))
    notification_event_type = _enum(
        "notification_event_type",
        ("new_task", "status_change"),
    )
    comment_kind.create(bind, checkfirst=True)
    notification_event_type.create(bind, checkfirst=True)

    op.drop_table("notifications")
    op.drop_table("history_events")
    op.drop_table("comments")

    op.create_table(
        "comments",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("approval_task_id", sa.Integer(), nullable=True),
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
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("request_id", sa.Integer(), nullable=False),
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
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("recipient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_id", sa.Integer(), nullable=True),
        sa.Column("approval_task_id", sa.Integer(), nullable=True),
        sa.Column("event_type", notification_event_type, nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column(
            "read",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
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
    """Restore empty Pre-E2 UUID audit/notification shells."""
    bind = op.get_bind()
    comment_kind = _enum("comment_kind", ("free", "decision"))
    notification_event_type = _enum(
        "notification_event_type",
        ("new_task", "status_change"),
    )
    comment_kind.create(bind, checkfirst=True)
    notification_event_type.create(bind, checkfirst=True)

    op.drop_table("notifications")
    op.drop_table("history_events")
    op.drop_table("comments")

    uuid_pk = lambda: sa.Column(  # noqa: E731
        "id",
        postgresql.UUID(as_uuid=True),
        server_default=sa.text("gen_random_uuid()"),
        nullable=False,
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
            ["author_id"],
            ["users.id"],
            name="fk_comments_author_id_users",
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
        sa.Column(
            "read",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
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
        sa.PrimaryKeyConstraint("id", name="pk_notifications"),
    )
    op.create_index("ix_notifications_recipient_id", "notifications", ["recipient_id"])
    op.create_index("ix_notifications_request_id", "notifications", ["request_id"])
    op.create_index(
        "ix_notifications_approval_task_id",
        "notifications",
        ["approval_task_id"],
    )
