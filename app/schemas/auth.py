"""Auth and current-user API schemas."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import RoleCode


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    login: str
    password: str


class CurrentUser(BaseModel):
    id: UUID
    login: str
    full_name: str
    email: str
    position: str | None
    department: str | None
    roles: list[RoleCode]


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token lifetime in seconds")
    user: CurrentUser
