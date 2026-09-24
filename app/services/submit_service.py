"""Legacy submit / cancel thin wrappers — business logic lives in Action Engine."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.domain.identity import User
from app.schemas.request import RequestCard
from app.services import action_engine


def submit_request(session: Session, user: User, request_id: int) -> RequestCard:
    action_id = action_engine.action_id_by_code(session, "submit")
    return action_engine.execute_action(session, user, request_id, action_id, comment=None)


def cancel_request(session: Session, user: User, request_id: int) -> RequestCard:
    action_id = action_engine.action_id_by_code(session, "cancel")
    return action_engine.execute_action(session, user, request_id, action_id, comment=None)
