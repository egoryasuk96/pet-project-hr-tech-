"""Fixtures for Stage 5.3 API tests. Require an isolated PostgreSQL (TEST_DATABASE_URL)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_engine, get_session_factory, reset_engine
from app.domain import (  # noqa: F401 — register tables
    ApprovalRoute,
    ApprovalStage,
    AssignmentKind,
    Dictionary,
    DictionaryItem,
    FieldDataType,
    RequestFieldDefinition,
    RequestType,
    Role,
    RoleCode,
    StageAssignment,
    User,
    UserRole,
)

TEST_PASSWORD = "test-pass-stage53"
JWT_SECRET = "test-jwt-secret-stage53-not-for-production"


@dataclass
class ApiDataset:
    employee_a_login: str
    employee_b_login: str
    approver_login: str
    vacation_type_id: UUID
    certificate_type_id: UUID
    inactive_type_id: UUID
    catalog_item_id: UUID


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is required for Stage 5.3 API tests (see README)")

    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("JWT_SECRET", JWT_SECRET)
    get_settings.cache_clear()
    reset_engine()

    engine = get_engine()
    Base.metadata.create_all(engine)

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client

    session = get_session_factory()()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(delete(table))
        session.commit()
    finally:
        session.close()
    reset_engine()
    get_settings.cache_clear()


@pytest.fixture
def dataset(client: TestClient) -> ApiDataset:
    session = get_session_factory()()
    try:
        roles = {code: Role(code=code) for code in RoleCode}
        for role in roles.values():
            session.add(role)
        session.flush()

        password_hash = hash_password(TEST_PASSWORD)

        def add_user(login: str, full_name: str, role_code: RoleCode) -> User:
            user = User(
                login=login,
                password_hash=password_hash,
                full_name=full_name,
                email=f"{login}@example.local",
                position="Test",
                department="IT",
                is_active=True,
            )
            session.add(user)
            session.flush()
            session.add(UserRole(user_id=user.id, role_id=roles[role_code].id))
            return user

        employee_a = add_user("employee.a", "Employee A", RoleCode.EMPLOYEE)
        employee_b = add_user("employee.b", "Employee B", RoleCode.EMPLOYEE)
        approver = add_user("approver.a", "Approver A", RoleCode.APPROVER)

        dictionary = Dictionary(name="Виды справок")
        session.add(dictionary)
        session.flush()
        catalog_item = DictionaryItem(
            dictionary_id=dictionary.id,
            code="employment",
            name="Справка с места работы",
            is_active=True,
        )
        session.add(catalog_item)
        session.flush()

        vacation = RequestType(
            name="Отпуск",
            description="Заявка на отпуск",
            is_active=True,
        )
        session.add(vacation)
        session.flush()
        session.add(
            RequestFieldDefinition(
                request_type_id=vacation.id,
                code="date_from",
                name="Дата начала",
                data_type=FieldDataType.DATE,
                required=True,
                order_no=1,
            )
        )
        session.add(
            RequestFieldDefinition(
                request_type_id=vacation.id,
                code="date_to",
                name="Дата окончания",
                data_type=FieldDataType.DATE,
                required=True,
                order_no=2,
            )
        )
        session.add(
            RequestFieldDefinition(
                request_type_id=vacation.id,
                code="comment",
                name="Комментарий",
                data_type=FieldDataType.TEXT,
                required=False,
                order_no=3,
            )
        )

        certificate = RequestType(
            name="Справка",
            description="Кадровая справка",
            is_active=True,
        )
        session.add(certificate)
        session.flush()
        session.add(
            RequestFieldDefinition(
                request_type_id=certificate.id,
                code="certificate_kind",
                name="Вид справки",
                data_type=FieldDataType.CATALOG,
                required=True,
                order_no=1,
                dictionary_id=dictionary.id,
            )
        )

        inactive = RequestType(name="Inactive", description="Hidden", is_active=False)
        session.add(inactive)
        session.flush()

        def add_route(request_type_id: UUID) -> None:
            route = ApprovalRoute(request_type_id=request_type_id)
            session.add(route)
            session.flush()
            stage = ApprovalStage(route_id=route.id, name="Согласование руководителем", sequence_no=1)
            session.add(stage)
            session.flush()
            session.add(
                StageAssignment(
                    stage_id=stage.id,
                    assignment_kind=AssignmentKind.USER,
                    user_id=approver.id,
                    role_id=None,
                )
            )

        add_route(vacation.id)
        add_route(certificate.id)

        session.commit()
        return ApiDataset(
            employee_a_login=employee_a.login,
            employee_b_login=employee_b.login,
            approver_login=approver.login,
            vacation_type_id=vacation.id,
            certificate_type_id=certificate.id,
            inactive_type_id=inactive.id,
            catalog_item_id=catalog_item.id,
        )
    finally:
        session.close()


def auth_header(client: TestClient, login: str, password: str = TEST_PASSWORD) -> dict[str, str]:
    response = client.post("/auth/login", json={"login": login, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
