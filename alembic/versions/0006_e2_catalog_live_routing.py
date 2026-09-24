"""E2 D: catalog + live routing → Integer PK; RequestType.process_id.

Revision ID: 0006_e2_catalog_live_routing
Revises: 0005_e2_rbac_user_employee
Create Date: 2026-09-23

Controlled wipe/recreate of catalog and live routing only (runtime already empty).
Preserves semantic config (dictionary items, type fields, routes, approver assignments)
with new Integer IDs. Links request_types to processes via process_id + code.

Does NOT alter users / roles / org / process *schema*.
May insert one Process row if processes is empty (required FK).
Does NOT migrate requests (still legacy UUID schema until Step E).
"""

from __future__ import annotations

from typing import Any, Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0006_e2_catalog_live_routing"
down_revision: Union[str, None] = "0005_e2_rbac_user_employee"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ASSIGNMENT_KIND_CHECK = (
    "(assignment_kind = 'role' AND role_id IS NOT NULL AND user_id IS NULL) "
    "OR (assignment_kind = 'user' AND user_id IS NOT NULL AND role_id IS NULL) "
    "OR (assignment_kind = 'role_and_user' AND role_id IS NOT NULL AND user_id IS NOT NULL)"
)

# Fallback codes when type name is not recognized.
TYPE_CODE_BY_NAME = {
    "Отпуск": "vacation",
    "Справка": "certificate",
}


def _enum(name: str, values: tuple[str, ...]) -> postgresql.ENUM:
    return postgresql.ENUM(*values, name=name, create_type=False)


def _snapshot_catalog(bind) -> dict[str, Any]:
    dictionaries = [
        dict(r._mapping)
        for r in bind.execute(sa.text("SELECT id, name FROM dictionaries ORDER BY name"))
    ]
    items = [
        dict(r._mapping)
        for r in bind.execute(
            sa.text(
                "SELECT dictionary_id, code, name, is_active AS active "
                "FROM dictionary_items ORDER BY dictionary_id, code"
            )
        )
    ]
    types = [
        dict(r._mapping)
        for r in bind.execute(
            sa.text(
                "SELECT id, name, description, is_active AS active "
                "FROM request_types ORDER BY name"
            )
        )
    ]
    fields = [
        dict(r._mapping)
        for r in bind.execute(
            sa.text(
                "SELECT request_type_id, code, name, data_type::text AS data_type, "
                "required, order_no, dictionary_id "
                "FROM request_field_definitions ORDER BY request_type_id, order_no"
            )
        )
    ]
    routes = [
        dict(r._mapping)
        for r in bind.execute(
            sa.text(
                """
                SELECT ar.id AS route_id, ar.request_type_id,
                       s.id AS stage_id, s.name AS stage_name, s.sequence_no,
                       sa.assignment_kind::text AS assignment_kind,
                       sa.role_id, sa.user_id
                FROM approval_routes ar
                JOIN approval_stages s ON s.route_id = ar.id
                LEFT JOIN stage_assignments sa ON sa.stage_id = s.id
                ORDER BY ar.request_type_id, s.sequence_no
                """
            )
        )
    ]
    return {
        "dictionaries": dictionaries,
        "items": items,
        "types": types,
        "fields": fields,
        "routes": routes,
    }


def _ensure_process_id(bind) -> int:
    process_id = bind.execute(sa.text("SELECT id FROM processes ORDER BY id LIMIT 1")).scalar()
    if process_id is not None:
        return int(process_id)
    return int(
        bind.execute(
            sa.text(
                """
                INSERT INTO processes (code, name, description, active)
                VALUES (
                  'employee_requests',
                  'Employee requests',
                  'Default process for employee service request types',
                  true
                )
                RETURNING id
                """
            )
        ).scalar_one()
    )


def _type_code(name: str, index: int) -> str:
    if name in TYPE_CODE_BY_NAME:
        return TYPE_CODE_BY_NAME[name]
    slug = "".join(ch.lower() if ch.isalnum() else "_" for ch in name).strip("_")
    return slug or f"type_{index}"


def upgrade() -> None:
    bind = op.get_bind()
    snapshot = _snapshot_catalog(bind)
    process_id = _ensure_process_id(bind)

    # Detach legacy requests from catalog (table kept until Step E; already empty).
    op.drop_constraint(
        "fk_requests_request_type_id_request_types",
        "requests",
        type_="foreignkey",
    )

    # Drop live routing then catalog (child → parent).
    op.drop_table("stage_assignments")
    op.drop_table("approval_stages")
    op.drop_table("approval_routes")
    op.drop_table("request_field_definitions")
    op.drop_table("dictionary_items")
    op.drop_table("dictionaries")
    op.drop_table("request_types")

    field_data_type = _enum("field_data_type", ("text", "date", "number", "catalog"))
    assignment_kind = _enum("assignment_kind", ("role", "user", "role_and_user"))
    field_data_type.create(bind, checkfirst=True)
    assignment_kind.create(bind, checkfirst=True)

    op.create_table(
        "dictionaries",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_dictionaries"),
    )

    op.create_table(
        "dictionary_items",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("dictionary_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["dictionary_id"],
            ["dictionaries.id"],
            name="fk_dictionary_items_dictionary_id_dictionaries",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_dictionary_items"),
        sa.UniqueConstraint(
            "dictionary_id",
            "code",
            name="uq_dictionary_items_dictionary_code",
        ),
    )

    op.create_table(
        "request_types",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("process_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["process_id"],
            ["processes.id"],
            name="fk_request_types_process_id_processes",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_request_types"),
        sa.UniqueConstraint("code", name="uq_request_types_code"),
    )
    op.create_index("ix_request_types_process_id", "request_types", ["process_id"])

    op.create_table(
        "request_field_definitions",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("request_type_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("data_type", field_data_type, nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False),
        sa.Column("order_no", sa.Integer(), nullable=False),
        sa.Column("dictionary_id", sa.Integer(), nullable=True),
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
            "request_type_id",
            "code",
            name="uq_request_field_definitions_type_code",
        ),
    )
    op.create_index(
        "ix_request_field_definitions_dictionary_id",
        "request_field_definitions",
        ["dictionary_id"],
    )

    op.create_table(
        "approval_routes",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("request_type_id", sa.Integer(), nullable=False),
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
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("route_id", sa.Integer(), nullable=False),
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
            "route_id",
            "sequence_no",
            name="uq_approval_stages_route_sequence",
        ),
    )

    op.create_table(
        "stage_assignments",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("stage_id", sa.Integer(), nullable=False),
        sa.Column("assignment_kind", assignment_kind, nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.CheckConstraint(
            "role_id IS NOT NULL OR user_id IS NOT NULL",
            name="ck_stage_assignments_role_or_user",
        ),
        sa.CheckConstraint(
            ASSIGNMENT_KIND_CHECK,
            name="ck_stage_assignments_kind_matches_fks",
        ),
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

    # --- reload semantic data with new Integer IDs ---
    old_dict_to_new: dict[Any, int] = {}
    for d in snapshot["dictionaries"]:
        new_id = bind.execute(
            sa.text("INSERT INTO dictionaries (name) VALUES (:name) RETURNING id"),
            {"name": d["name"]},
        ).scalar_one()
        old_dict_to_new[d["id"]] = int(new_id)

    for item in snapshot["items"]:
        bind.execute(
            sa.text(
                """
                INSERT INTO dictionary_items (dictionary_id, code, name, active)
                VALUES (:dictionary_id, :code, :name, :active)
                """
            ),
            {
                "dictionary_id": old_dict_to_new[item["dictionary_id"]],
                "code": item["code"],
                "name": item["name"],
                "active": bool(item["active"]),
            },
        )

    old_type_to_new: dict[Any, int] = {}
    for index, t in enumerate(snapshot["types"], start=1):
        code = _type_code(t["name"], index)
        new_id = bind.execute(
            sa.text(
                """
                INSERT INTO request_types (process_id, code, name, description, active)
                VALUES (:process_id, :code, :name, :description, :active)
                RETURNING id
                """
            ),
            {
                "process_id": process_id,
                "code": code,
                "name": t["name"],
                "description": t["description"],
                "active": bool(t["active"]),
            },
        ).scalar_one()
        old_type_to_new[t["id"]] = int(new_id)

    for field in snapshot["fields"]:
        dict_id = field["dictionary_id"]
        bind.execute(
            sa.text(
                """
                INSERT INTO request_field_definitions (
                  request_type_id, code, name, data_type, required, order_no, dictionary_id
                ) VALUES (
                  :request_type_id, :code, :name, :data_type, :required, :order_no, :dictionary_id
                )
                """
            ),
            {
                "request_type_id": old_type_to_new[field["request_type_id"]],
                "code": field["code"],
                "name": field["name"],
                "data_type": field["data_type"],
                "required": bool(field["required"]),
                "order_no": field["order_no"],
                "dictionary_id": old_dict_to_new[dict_id] if dict_id is not None else None,
            },
        )

    # Group route rows by old request_type_id + stage
    routes_by_type: dict[Any, list[dict[str, Any]]] = {}
    for row in snapshot["routes"]:
        routes_by_type.setdefault(row["request_type_id"], []).append(row)

    for old_type_id, rows in routes_by_type.items():
        new_type_id = old_type_to_new[old_type_id]
        route_id = bind.execute(
            sa.text(
                "INSERT INTO approval_routes (request_type_id) "
                "VALUES (:request_type_id) RETURNING id"
            ),
            {"request_type_id": new_type_id},
        ).scalar_one()

        stages_seen: dict[int, int] = {}
        for row in rows:
            seq = int(row["sequence_no"])
            if seq not in stages_seen:
                stage_id = bind.execute(
                    sa.text(
                        """
                        INSERT INTO approval_stages (route_id, name, sequence_no)
                        VALUES (:route_id, :name, :sequence_no)
                        RETURNING id
                        """
                    ),
                    {
                        "route_id": route_id,
                        "name": row["stage_name"],
                        "sequence_no": seq,
                    },
                ).scalar_one()
                stages_seen[seq] = int(stage_id)
            stage_id = stages_seen[seq]
            if row["assignment_kind"] is None:
                continue
            bind.execute(
                sa.text(
                    """
                    INSERT INTO stage_assignments (
                      stage_id, assignment_kind, role_id, user_id
                    ) VALUES (
                      :stage_id, :assignment_kind, :role_id, :user_id
                    )
                    """
                ),
                {
                    "stage_id": stage_id,
                    "assignment_kind": row["assignment_kind"],
                    "role_id": row["role_id"],
                    "user_id": row["user_id"],
                },
            )


def downgrade() -> None:
    """Restore Pre-E2 UUID catalog/routing shells (empty). Data remapped IDs not restored."""
    bind = op.get_bind()
    field_data_type = _enum("field_data_type", ("text", "date", "number", "catalog"))
    assignment_kind = _enum("assignment_kind", ("role", "user", "role_and_user"))

    op.drop_table("stage_assignments")
    op.drop_table("approval_stages")
    op.drop_table("approval_routes")
    op.drop_table("request_field_definitions")
    op.drop_table("request_types")
    op.drop_table("dictionary_items")
    op.drop_table("dictionaries")

    uuid_pk = lambda: sa.Column(  # noqa: E731
        "id",
        postgresql.UUID(as_uuid=True),
        server_default=sa.text("gen_random_uuid()"),
        nullable=False,
    )

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
            "dictionary_id",
            "code",
            name="uq_dictionary_items_dictionary_code",
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
            "request_type_id",
            "code",
            name="uq_request_field_definitions_type_code",
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
            "route_id",
            "sequence_no",
            name="uq_approval_stages_route_sequence",
        ),
    )
    op.create_table(
        "stage_assignments",
        uuid_pk(),
        sa.Column("stage_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assignment_kind", assignment_kind, nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.CheckConstraint(
            "role_id IS NOT NULL OR user_id IS NOT NULL",
            name="ck_stage_assignments_role_or_user",
        ),
        sa.CheckConstraint(
            ASSIGNMENT_KIND_CHECK,
            name="ck_stage_assignments_kind_matches_fks",
        ),
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

    # Re-attach requests.request_type_id FK (legacy UUID column still present until E).
    op.create_foreign_key(
        "fk_requests_request_type_id_request_types",
        "requests",
        "request_types",
        ["request_type_id"],
        ["id"],
        ondelete="RESTRICT",
    )
