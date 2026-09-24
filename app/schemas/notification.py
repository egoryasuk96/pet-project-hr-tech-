"""Target read schemas for Notification (E5.1)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import NotificationEventType


class NotificationResponse(BaseModel):
    id: int
    request_id: int | None
    approval_task_id: int | None
    event_type: NotificationEventType
    text: str
    read: bool
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse] = Field(default_factory=list)
