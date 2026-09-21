"""Add immutable created_at to approval_tasks (OQ-04 / ERD C-16).

Revision ID: 0002_approval_task_created_at
Revises: 0001_stage52_domain
Create Date: 2026-09-21

Existing rows receive created_at = now() via column server_default
during ADD COLUMN ... NOT NULL.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_approval_task_created_at"
down_revision: Union[str, None] = "0001_stage52_domain"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "approval_tasks",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("approval_tasks", "created_at")
