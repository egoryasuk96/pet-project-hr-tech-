"""E2 B: create Target org and process configuration tables.

Revision ID: 0004_e2_org_process_tables
Revises: 0003_e2_drop_runtime_snapshot
Create Date: 2026-09-23

Creates Integer-PK tables:
  companies, departments, employees,
  processes, statuses, actions, process_transitions.

process_transitions.role_id is INTEGER NOT NULL without FK to roles:
legacy roles.id is still UUID until Step C (RBAC int roles). FK to roles
is deferred intentionally for the mixed A–B schema state.

Creates PG enum process_transition_effect.
Does NOT seed data. Does NOT alter users / user_roles / catalog / routing.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0004_e2_org_process_tables"
down_revision: Union[str, None] = "0003_e2_drop_runtime_snapshot"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PROCESS_TRANSITION_EFFECT_VALUES = ("status_only", "approve_advance")


def upgrade() -> None:
    bind = op.get_bind()
    effect_enum = postgresql.ENUM(
        *PROCESS_TRANSITION_EFFECT_VALUES,
        name="process_transition_effect",
    )
    effect_enum.create(bind, checkfirst=False)

    effect_col = postgresql.ENUM(
        *PROCESS_TRANSITION_EFFECT_VALUES,
        name="process_transition_effect",
        create_type=False,
    )

    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_companies"),
    )

    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_departments_company_id_companies",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_departments"),
    )
    op.create_index("ix_departments_company_id", "departments", ["company_id"])

    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("employee_number", sa.String(), nullable=False),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=False),
        sa.Column("middle_name", sa.String(), nullable=True),
        sa.Column("department_id", sa.Integer(), nullable=False),
        sa.Column("manager_employee_id", sa.Integer(), nullable=True),
        sa.Column("position", sa.String(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["department_id"],
            ["departments.id"],
            name="fk_employees_department_id_departments",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["manager_employee_id"],
            ["employees.id"],
            name="fk_employees_manager_employee_id_employees",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_employees"),
        sa.UniqueConstraint("employee_number", name="uq_employees_employee_number"),
    )
    op.create_index("ix_employees_department_id", "employees", ["department_id"])
    op.create_index(
        "ix_employees_manager_employee_id",
        "employees",
        ["manager_employee_id"],
    )

    op.create_table(
        "processes",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_processes"),
        sa.UniqueConstraint("code", name="uq_processes_code"),
    )

    op.create_table(
        "statuses",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_statuses"),
        sa.UniqueConstraint("code", name="uq_statuses_code"),
    )

    op.create_table(
        "actions",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_actions"),
        sa.UniqueConstraint("code", name="uq_actions_code"),
    )

    op.create_table(
        "process_transitions",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("process_id", sa.Integer(), nullable=False),
        sa.Column("from_status_id", sa.Integer(), nullable=False),
        sa.Column("action_id", sa.Integer(), nullable=False),
        sa.Column("to_status_id", sa.Integer(), nullable=False),
        # Integer role_id without FK: roles.id is still UUID until Step C.
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("effect", effect_col, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["process_id"],
            ["processes.id"],
            name="fk_process_transitions_process_id_processes",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["from_status_id"],
            ["statuses.id"],
            name="fk_process_transitions_from_status_id_statuses",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["action_id"],
            ["actions.id"],
            name="fk_process_transitions_action_id_actions",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["to_status_id"],
            ["statuses.id"],
            name="fk_process_transitions_to_status_id_statuses",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_process_transitions"),
    )
    op.create_index(
        "ix_process_transitions_process_id",
        "process_transitions",
        ["process_id"],
    )
    op.create_index(
        "ix_process_transitions_from_status_id",
        "process_transitions",
        ["from_status_id"],
    )
    op.create_index(
        "ix_process_transitions_action_id",
        "process_transitions",
        ["action_id"],
    )
    op.create_index(
        "ix_process_transitions_to_status_id",
        "process_transitions",
        ["to_status_id"],
    )
    op.create_index(
        "ix_process_transitions_role_id",
        "process_transitions",
        ["role_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_process_transitions_role_id", table_name="process_transitions")
    op.drop_index("ix_process_transitions_to_status_id", table_name="process_transitions")
    op.drop_index("ix_process_transitions_action_id", table_name="process_transitions")
    op.drop_index(
        "ix_process_transitions_from_status_id",
        table_name="process_transitions",
    )
    op.drop_index("ix_process_transitions_process_id", table_name="process_transitions")
    op.drop_table("process_transitions")

    op.drop_table("actions")
    op.drop_table("statuses")
    op.drop_table("processes")

    op.drop_index("ix_employees_manager_employee_id", table_name="employees")
    op.drop_index("ix_employees_department_id", table_name="employees")
    op.drop_table("employees")

    op.drop_index("ix_departments_company_id", table_name="departments")
    op.drop_table("departments")
    op.drop_table("companies")

    bind = op.get_bind()
    postgresql.ENUM(
        *PROCESS_TRANSITION_EFFECT_VALUES,
        name="process_transition_effect",
    ).drop(bind, checkfirst=False)
