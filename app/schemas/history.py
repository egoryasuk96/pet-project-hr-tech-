"""Target read schemas for HistoryEvent (E5.1)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class HistoryEventResponse(BaseModel):
    id: int
    action: str
    actor_id: UUID | None
    from_state: str | None
    to_state: str | None
    comment: str | None
    at: datetime


class HistoryEventListResponse(BaseModel):
    items: list[HistoryEventResponse] = Field(default_factory=list)
