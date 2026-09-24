"""Read-only HistoryEvent queries (E5.1 / FR-AUDIT-01)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import not_found
from app.domain.audit import HistoryEvent
from app.domain.identity import User
from app.domain.request import Request
from app.schemas.history import HistoryEventListResponse, HistoryEventResponse
from app.services.request_service import can_view_request


def list_request_history(
    session: Session,
    user: User,
    request_id: int,
) -> HistoryEventListResponse:
    request = session.get(Request, request_id)
    if request is None or not can_view_request(session, user, request):
        raise not_found()

    rows = session.scalars(
        select(HistoryEvent)
        .where(HistoryEvent.request_id == request_id)
        .order_by(HistoryEvent.at.desc(), HistoryEvent.id.desc())
    ).all()

    return HistoryEventListResponse(
        items=[
            HistoryEventResponse(
                id=row.id,
                action=row.action,
                actor_id=row.actor_id,
                from_state=row.from_state,
                to_state=row.to_state,
                comment=row.comment,
                at=row.at,
            )
            for row in rows
        ]
    )
