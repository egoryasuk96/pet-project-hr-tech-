"""FastAPI dependencies: DB session, JWT current user, RBAC."""

from __future__ import annotations

from collections.abc import Callable

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.errors import forbidden, unauthorized
from app.core.security import decode_access_token
from app.db.session import get_db
from app.domain.enums import RoleCode
from app.domain.identity import User, UserRole

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise unauthorized()
    try:
        user_id = decode_access_token(credentials.credentials, get_settings())
    except (jwt.PyJWTError, ValueError):
        raise unauthorized() from None
    user = session.scalar(
        select(User)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
        .where(User.id == user_id)
    )
    if user is None or not user.is_active:
        raise unauthorized()
    return user


def require_roles(*codes: RoleCode) -> Callable[..., User]:
    def _dependency(user: User = Depends(get_current_user)) -> User:
        have = {item.role.code for item in user.user_roles}
        if have.isdisjoint(codes):
            raise forbidden()
        return user

    return _dependency
