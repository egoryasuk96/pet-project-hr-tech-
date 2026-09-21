"""Authentication: login and current-user mapping."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings
from app.core.errors import forbidden, invalid_credentials
from app.core.security import create_access_token, verify_password
from app.domain.identity import User, UserRole
from app.schemas.auth import CurrentUser, LoginResponse


def _user_options() -> tuple:
    return (selectinload(User.user_roles).selectinload(UserRole.role),)


def load_user_by_login(session: Session, login: str) -> User | None:
    return session.scalar(
        select(User).options(*_user_options()).where(User.login == login)
    )


def to_current_user(user: User) -> CurrentUser:
    roles = sorted({item.role.code for item in user.user_roles}, key=lambda code: code.value)
    return CurrentUser(
        id=user.id,
        login=user.login,
        full_name=user.full_name,
        email=user.email,
        position=user.position,
        department=user.department,
        roles=list(roles),
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
