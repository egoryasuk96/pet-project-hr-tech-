"""E2 C: RBAC User.role_id + Employee link; Integer roles.

Revision ID: 0005_e2_rbac_user_employee
Revises: 0004_e2_org_process_tables
Create Date: 2026-09-23

- Recreate roles with Integer PK (employee / approver / admin + name).
- Preserve existing users (UUID id, login, password_hash, is_active).
- Map user_roles → users.role_id (priority admin > approver > employee).
- Create employees from legacy user profile fields; set users.employee_id.
- Drop user_roles and legacy profile columns on users.
- Convert stage_assignments.role_id UUID → Integer (nullable) for FK to new roles.
- Add FK process_transitions.role_id → roles.id (deferred in Step B).

Does NOT seed catalog/requests. Does NOT recreate demo users.
Email has no Target column (ERD) and is not persisted after upgrade.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0005_e2_rbac_user_employee"
down_revision: Union[str, None] = "0004_e2_org_process_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ROLE_NAMES: dict[str, str] = {
    "employee": "Сотрудник",
    "approver": "Согласующий",
    "admin": "Администратор",
}

ROLE_PRIORITY_SQL = """
CASE r.code::text
  WHEN 'admin' THEN 1
  WHEN 'approver' THEN 2
  WHEN 'employee' THEN 3
  ELSE 99
END
"""


def _split_full_name(full_name: str) -> tuple[str, str | None, str]:
    parts = [p for p in (full_name or "").strip().split() if p]
    if not parts:
        return ("Unknown", None, "User")
    if len(parts) == 1:
        return (parts[0], None, parts[0])
    if len(parts) == 2:
        return (parts[0], None, parts[1])
    return (parts[0], " ".join(parts[1:-1]), parts[-1])


def upgrade() -> None:
    bind = op.get_bind()
    role_code = postgresql.ENUM(
        "employee",
        "approver",
        "admin",
        name="role_code",
        create_type=False,
    )

    # --- minimal org for Employee.department_id (not a full app seed) ---
    company_id = bind.execute(sa.text("SELECT id FROM companies LIMIT 1")).scalar()
    if company_id is None:
        company_id = bind.execute(
            sa.text(
                "INSERT INTO companies (name, active) "
                "VALUES ('Demo Company', true) RETURNING id"
            )
        ).scalar_one()

    dept_rows = list(
        bind.execute(sa.text("SELECT DISTINCT department FROM users WHERE department IS NOT NULL"))
    )
    dept_names = sorted({row[0] for row in dept_rows if row[0]}) or ["General"]
    dept_id_by_name: dict[str, int] = {}
    for name in dept_names:
        existing = bind.execute(
            sa.text(
                "SELECT id FROM departments WHERE company_id = :cid AND name = :name"
            ),
            {"cid": company_id, "name": name},
        ).scalar()
        if existing is None:
            existing = bind.execute(
                sa.text(
                    "INSERT INTO departments (company_id, name, active) "
                    "VALUES (:cid, :name, true) RETURNING id"
                ),
                {"cid": company_id, "name": name},
            ).scalar_one()
        dept_id_by_name[name] = int(existing)

    default_dept_id = next(iter(dept_id_by_name.values()))

    # --- roles_new (Integer PK) ---
    op.create_table(
        "roles_new",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("code", role_code, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_roles_new"),
        sa.UniqueConstraint("code", name="uq_roles_new_code"),
    )
    for code, name in ROLE_NAMES.items():
        bind.execute(
            sa.text("INSERT INTO roles_new (code, name) VALUES (:code, :name)"),
            {"code": code, "name": name},
        )

    # --- users: add Target FKs (nullable until backfilled) ---
    op.add_column("users", sa.Column("role_id", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("employee_id", sa.Integer(), nullable=True))

    bind.execute(
        sa.text(
            f"""
            UPDATE users AS u
            SET role_id = sub.new_role_id
            FROM (
              SELECT DISTINCT ON (ur.user_id)
                     ur.user_id,
                     rn.id AS new_role_id
              FROM user_roles AS ur
              JOIN roles AS r ON r.id = ur.role_id
              JOIN roles_new AS rn ON rn.code = r.code
              ORDER BY ur.user_id, {ROLE_PRIORITY_SQL}
            ) AS sub
            WHERE u.id = sub.user_id
            """
        )
    )

    missing_role = bind.execute(
        sa.text("SELECT count(*) FROM users WHERE role_id IS NULL")
    ).scalar_one()
    if missing_role:
        raise RuntimeError(f"Step C: {missing_role} users have no mappable role_id")

    # --- employees from legacy profile fields ---
    users = list(
        bind.execute(
            sa.text(
                "SELECT id, login, full_name, position, department, is_active "
                "FROM users ORDER BY login"
            )
        )
    )
    for row in users:
        first_name, middle_name, last_name = _split_full_name(row.full_name)
        dept_name = row.department if row.department in dept_id_by_name else None
        department_id = dept_id_by_name.get(dept_name, default_dept_id)
        employee_id = bind.execute(
            sa.text(
                """
                INSERT INTO employees (
                  employee_number, first_name, last_name, middle_name,
                  department_id, manager_employee_id, position, active
                ) VALUES (
                  :employee_number, :first_name, :last_name, :middle_name,
                  :department_id, NULL, :position, :active
                )
                RETURNING id
                """
            ),
            {
                "employee_number": f"EMP-{row.login}",
                "first_name": first_name,
                "last_name": last_name,
                "middle_name": middle_name,
                "department_id": department_id,
                "position": row.position,
                "active": bool(row.is_active),
            },
        ).scalar_one()
        bind.execute(
            sa.text("UPDATE users SET employee_id = :eid WHERE id = :uid"),
            {"eid": employee_id, "uid": row.id},
        )

    missing_emp = bind.execute(
        sa.text("SELECT count(*) FROM users WHERE employee_id IS NULL")
    ).scalar_one()
    if missing_emp:
        raise RuntimeError(f"Step C: {missing_emp} users have no employee_id")

    # --- stage_assignments.role_id: UUID → Integer (currently all NULL) ---
    op.drop_constraint(
        "fk_stage_assignments_role_id_roles",
        "stage_assignments",
        type_="foreignkey",
    )
    op.drop_index("ix_stage_assignments_role_id", table_name="stage_assignments")
    op.drop_column("stage_assignments", "role_id")
    op.add_column(
        "stage_assignments",
        sa.Column("role_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_stage_assignments_role_id",
        "stage_assignments",
        ["role_id"],
    )

    # --- drop M:N and old UUID roles ---
    op.drop_table("user_roles")
    op.drop_table("roles")
    op.rename_table("roles_new", "roles")
    op.execute(sa.text("ALTER TABLE roles RENAME CONSTRAINT pk_roles_new TO pk_roles"))
    op.execute(sa.text("ALTER TABLE roles RENAME CONSTRAINT uq_roles_new_code TO uq_roles_code"))

    # --- finalize users Target shape ---
    op.alter_column("users", "role_id", existing_type=sa.Integer(), nullable=False)
    op.alter_column("users", "employee_id", existing_type=sa.Integer(), nullable=False)
    op.create_index("ix_users_role_id", "users", ["role_id"])
    op.create_index("ix_users_employee_id", "users", ["employee_id"])
    op.create_unique_constraint("uq_users_employee_id", "users", ["employee_id"])
    op.create_foreign_key(
        "fk_users_role_id_roles",
        "users",
        "roles",
        ["role_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_users_employee_id_employees",
        "users",
        "employees",
        ["employee_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.drop_column("users", "full_name")
    op.drop_column("users", "email")
    op.drop_column("users", "position")
    op.drop_column("users", "department")

    op.create_foreign_key(
        "fk_stage_assignments_role_id_roles",
        "stage_assignments",
        "roles",
        ["role_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_process_transitions_role_id_roles",
        "process_transitions",
        "roles",
        ["role_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    """Best-effort restore of UUID roles + user_roles + profile columns (dev)."""
    bind = op.get_bind()
    role_code = postgresql.ENUM(
        "employee",
        "approver",
        "admin",
        name="role_code",
        create_type=False,
    )

    op.drop_constraint(
        "fk_process_transitions_role_id_roles",
        "process_transitions",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_stage_assignments_role_id_roles",
        "stage_assignments",
        type_="foreignkey",
    )

    op.add_column("users", sa.Column("full_name", sa.String(), nullable=True))
    op.add_column("users", sa.Column("email", sa.String(), nullable=True))
    op.add_column("users", sa.Column("position", sa.String(), nullable=True))
    op.add_column("users", sa.Column("department", sa.String(), nullable=True))

    bind.execute(
        sa.text(
            """
            UPDATE users AS u
            SET
              full_name = trim(both ' ' FROM concat_ws(' ', e.first_name, e.middle_name, e.last_name)),
              position = e.position,
              department = d.name,
              email = u.login || '@example.local'
            FROM employees AS e
            JOIN departments AS d ON d.id = e.department_id
            WHERE u.employee_id = e.id
            """
        )
    )
    op.alter_column("users", "full_name", existing_type=sa.String(), nullable=False)
    op.alter_column("users", "email", existing_type=sa.String(), nullable=False)

    op.drop_constraint("fk_users_employee_id_employees", "users", type_="foreignkey")
    op.drop_constraint("fk_users_role_id_roles", "users", type_="foreignkey")
    op.drop_constraint("uq_users_employee_id", "users", type_="unique")
    op.drop_index("ix_users_employee_id", table_name="users")
    op.drop_index("ix_users_role_id", table_name="users")

    # Snapshot int role_id before swapping roles table.
    user_role_codes = list(
        bind.execute(
            sa.text(
                "SELECT u.id AS user_id, r.code::text AS code "
                "FROM users u JOIN roles r ON r.id = u.role_id"
            )
        )
    )
    employee_ids = [
        row[0]
        for row in bind.execute(sa.text("SELECT employee_id FROM users WHERE employee_id IS NOT NULL"))
    ]

    op.drop_column("users", "employee_id")
    op.drop_column("users", "role_id")

    op.rename_table("roles", "roles_new")
    op.create_table(
        "roles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("code", role_code, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_roles"),
        sa.UniqueConstraint("code", name="uq_roles_code"),
    )
    for code in ROLE_NAMES:
        bind.execute(
            sa.text("INSERT INTO roles (code) VALUES (:code)"),
            {"code": code},
        )

    op.create_table(
        "user_roles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_user_roles_user_id_users",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
            name="fk_user_roles_role_id_roles",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", "role_id", name="pk_user_roles"),
    )
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"])

    for row in user_role_codes:
        bind.execute(
            sa.text(
                """
                INSERT INTO user_roles (user_id, role_id)
                SELECT :uid, r.id FROM roles r WHERE r.code::text = :code
                """
            ),
            {"uid": row.user_id, "code": row.code},
        )

    op.drop_table("roles_new")

    # Restore stage_assignments.role_id as UUID (all NULL in current data path).
    op.drop_index("ix_stage_assignments_role_id", table_name="stage_assignments")
    op.drop_column("stage_assignments", "role_id")
    op.add_column(
        "stage_assignments",
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "ix_stage_assignments_role_id",
        "stage_assignments",
        ["role_id"],
    )
    op.create_foreign_key(
        "fk_stage_assignments_role_id_roles",
        "stage_assignments",
        "roles",
        ["role_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    # Remove employees created for these users (and leave empty org tables).
    if employee_ids:
        bind.execute(
            sa.text("DELETE FROM employees WHERE id = ANY(:ids)"),
            {"ids": employee_ids},
        )
