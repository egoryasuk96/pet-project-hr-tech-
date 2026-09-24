"""E4.2.0: extend notification_event_type with Target action event codes.

Revision ID: 0010_e2_extend_notif_enum
Revises: 0009_e2_drop_unused_enums
Create Date: 2026-09-23

Adds five Target values used by Action Engine notifications (E4.2):
  request_submitted, request_approved, request_rejected,
  request_returned, request_cancelled

Keeps existing values: new_task, status_change.

Does NOT alter the notifications table structure.
Does NOT remove or rename other enums.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "0010_e2_extend_notif_enum"
down_revision: Union[str, None] = "0009_e2_drop_unused_enums"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_VALUES: tuple[str, ...] = (
    "request_submitted",
    "request_approved",
    "request_rejected",
    "request_returned",
    "request_cancelled",
)

LEGACY_VALUES: tuple[str, ...] = (
    "new_task",
    "status_change",
)


def upgrade() -> None:
    for value in NEW_VALUES:
        # PostgreSQL 12+: ADD VALUE is transactional; IF NOT EXISTS keeps re-runs safe.
        op.execute(
            text(f"ALTER TYPE notification_event_type ADD VALUE IF NOT EXISTS '{value}'")
        )


def downgrade() -> None:
    """Restore enum to {new_task, status_change} only if no rows use extended values."""
    bind = op.get_bind()
    placeholders = ", ".join(f"'{v}'" for v in NEW_VALUES)
    count = bind.execute(
        text(
            f"""
            SELECT COUNT(*) FROM notifications
            WHERE event_type::text IN ({placeholders})
            """
        )
    ).scalar()
    if count:
        raise RuntimeError(
            f"Cannot downgrade notification_event_type: {count} row(s) in "
            "notifications still use extended values "
            f"({', '.join(NEW_VALUES)}). Remap or delete those rows first."
        )

    op.execute(text("ALTER TYPE notification_event_type RENAME TO notification_event_type_old"))
    legacy = ", ".join(f"'{v}'" for v in LEGACY_VALUES)
    op.execute(text(f"CREATE TYPE notification_event_type AS ENUM ({legacy})"))
    op.execute(
        text(
            """
            ALTER TABLE notifications
            ALTER COLUMN event_type TYPE notification_event_type
            USING event_type::text::notification_event_type
            """
        )
    )
    op.execute(text("DROP TYPE notification_event_type_old"))
