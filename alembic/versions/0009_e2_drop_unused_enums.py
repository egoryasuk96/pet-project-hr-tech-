"""E2 F: drop unused PostgreSQL enum types.

Revision ID: 0009_e2_drop_unused_enums
Revises: 0008_e2_audit_notifications
Create Date: 2026-09-23

Drops only enums with zero column dependencies after Target migrations:
  - request_status (Request now uses statuses.id)
  - approval_decision (ApprovalTask no longer has decision)

Keeps Target-used enums:
  approval_task_status, assignment_kind, comment_kind, field_data_type,
  notification_event_type, process_transition_effect, role_code.

Does NOT alter tables, columns, FKs, or data.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009_e2_drop_unused_enums"
down_revision: Union[str, None] = "0008_e2_audit_notifications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UNUSED_ENUMS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "request_status",
        ("draft", "in_approval", "returned", "approved", "rejected", "cancelled"),
    ),
    (
        "approval_decision",
        ("approve", "reject", "return"),
    ),
)


def upgrade() -> None:
    bind = op.get_bind()
    for name, values in UNUSED_ENUMS:
        postgresql.ENUM(*values, name=name).drop(bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    for name, values in UNUSED_ENUMS:
        postgresql.ENUM(*values, name=name).create(bind, checkfirst=True)
