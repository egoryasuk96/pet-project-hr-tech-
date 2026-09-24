"""Shared API schemas (error envelope and pagination constants)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Target nested envelope (ADR-ERR-03)."""

    error: ErrorBody
