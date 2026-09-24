"""Authentication: login and current-user mapping (Target User.role_id)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings
from app.core.errors import forbidden, invalid_credentials
from app.core.security import create_access_token, verify_password
from app.domain.identity import User
from app.domain.org import Employee
from app.schemas.auth import CurrentUser, LoginResponse


def _user_options() -> tuple:
    return (
        selectinload(User.role),
        selectinload(User.employee).selectinload(Employee.department),
    )


def load_user_by_login(session: Session, login: str) -> User | None:
    return session.scalar(
        select(User).options(*_user_options()).where(User.login == login)
    )


def _employee_full_name(employee: Employee | None) -> str:
    if employee is None:
        return ""
    parts = [employee.first_name, employee.middle_name, employee.last_name]
    return " ".join(part for part in parts if part)


def to_current_user(user: User) -> CurrentUser:
    employee = user.employee
    department_name = None
    if employee is not None and employee.department is not None:
        department_name = employee.department.name
    role_codes = [user.role.code] if user.role is not None else []
    return CurrentUser(
        id=user.id,
        login=user.login,
        full_name=_employee_full_name(employee),
        email=None,
        position=employee.position if employee is not None else None,
        department=department_name,
        roles=role_codes,
    )


def login(session: Session, *, login_name: str, password: str, settings: Settings) -> LoginResponse:
    user = load_user_by_login(session, login_name)
    if user is None or not user.password_hash:
        raise invalid_credentials()
    if not verify_password(password, user.password_hash):
        raise invalid_credentials()
    if not user.is_active:
        raise forbidden()
    token = create_access_token(user_id=user.id, settings=settings)
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.jwt_ttl_hours * 3600,
        user=to_current_user(user),
    )
