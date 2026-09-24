"""Read-only available actions from ProcessTransition (E3.1 — no execution)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import not_found
from app.domain.identity import User
from app.domain.process import Action, ProcessTransition
from app.domain.request import Request
from app.schemas.request import ActionOut, AvailableActionsResponse
from app.services.request_service import can_view_request


def list_available_actions(
    session: Session,
    user: User,
    request_id: int,
) -> AvailableActionsResponse:
    """Compute actions from live ProcessTransition filtered by user role.

    Visibility matches GET /requests/{id} (BR-01 / BR-14).
    Does not apply self-approval / assignee checks (Action Engine responsibility).
    """
    request = session.scalar(
        select(Request)
        .options(selectinload(Request.request_type))
        .where(Request.id == request_id)
    )
    if request is None or not can_view_request(session, user, request):
        raise not_found()
    process_id = request.request_type.process_id

    transitions = session.scalars(
        select(ProcessTransition)
        .options(selectinload(ProcessTransition.action))
        .where(
            ProcessTransition.process_id == process_id,
            ProcessTransition.from_status_id == request.status_id,
            ProcessTransition.role_id == role_id_of(user),
            ProcessTransition.is_active.is_(True),
        )
        .order_by(ProcessTransition.sort_order, ProcessTransition.id)
    ).all()

    actions: list[ActionOut] = []
    seen: set[int] = set()
    for transition in transitions:
        action: Action = transition.action
        if not action.active or action.id in seen:
            continue
        seen.add(action.id)
        actions.append(ActionOut(id=action.id, code=action.code, name=action.name))

    return AvailableActionsResponse(available_actions=actions)


def role_id_of(user: User) -> int:
    return user.role_id
