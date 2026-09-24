"""Fixtures for Target E2 API tests. Require isolated PostgreSQL (TEST_DATABASE_URL)."""

from __future__ import annotations

import os
from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.config import get_settings
from app.db.base import Base
from app.db.seed import seed
from app.db.session import get_engine, get_session_factory, reset_engine
from app.domain import (  # noqa: F401 — register Target tables
    Action,
    RequestType,
    Role,
    Status,
    User,
)

TEST_PASSWORD = "test-pass-e31"
JWT_SECRET = "test-jwt-secret-e31-not-for-production"

VALID_VACATION_DATES = {"date_from": "2026-06-01", "date_to": "2026-06-14"}


def set_request_field_values(request_id: int, values: dict[str, str | None]) -> None:
    """Upsert RequestFieldValue rows for tests (no PATCH API yet)."""
    from app.domain.request import RequestFieldValue

    session = get_session_factory()()
    try:
        for field_code, value in values.items():
            row = session.scalar(
                select(RequestFieldValue).where(
                    RequestFieldValue.request_id == request_id,
                    RequestFieldValue.field_code == field_code,
                )
            )
            if row is None:
                session.add(
                    RequestFieldValue(
                        request_id=request_id,
                        field_code=field_code,
                        value=value,
                    )
                )
            else:
                row.value = value
        session.commit()
    finally:
        session.close()


def fill_valid_vacation_fields(request_id: int) -> None:
    set_request_field_values(request_id, dict(VALID_VACATION_DATES))


@dataclass
class ApiDataset:
    employee_login: str
    approver_login: str
    admin_login: str
    vacation_type_id: int
    certificate_type_id: int
    draft_status_id: int
    in_approval_status_id: int
    returned_status_id: int
    submit_action_id: int
    cancel_action_id: int
    approve_action_id: int
    reject_action_id: int
    return_action_id: int


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is required for API tests (see README)")

    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("JWT_SECRET", JWT_SECRET)
    monkeypatch.setenv("DEMO_PASSWORD", TEST_PASSWORD)
    get_settings.cache_clear()
    reset_engine()

    engine = get_engine()
    # Fresh schema avoids leftover indexes/enums between suites
    from sqlalchemy import text

    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    Base.metadata.create_all(engine)

    session = get_session_factory()()
    try:
        seed(session)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

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
        vacation = session.scalar(select(RequestType).where(RequestType.code == "vacation"))
        certificate = session.scalar(select(RequestType).where(RequestType.code == "certificate"))
        draft = session.scalar(select(Status).where(Status.code == "draft"))
        in_approval = session.scalar(select(Status).where(Status.code == "in_approval"))
        returned = session.scalar(select(Status).where(Status.code == "returned"))
        actions = {
            row.code: row.id
            for row in session.scalars(select(Action)).all()
        }
        assert vacation and certificate and draft and in_approval and returned
        return ApiDataset(
            employee_login="employee.demo",
            approver_login="approver.demo",
            admin_login="admin.demo",
            vacation_type_id=vacation.id,
            certificate_type_id=certificate.id,
            draft_status_id=draft.id,
            in_approval_status_id=in_approval.id,
            returned_status_id=returned.id,
            submit_action_id=actions["submit"],
            cancel_action_id=actions["cancel"],
            approve_action_id=actions["approve"],
            reject_action_id=actions["reject"],
            return_action_id=actions["return"],
        )
    finally:
        session.close()


def auth_header(client: TestClient, login: str, password: str = TEST_PASSWORD) -> dict[str, str]:
    response = client.post("/auth/login", json={"login": login, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
