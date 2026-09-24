"""Target request read/create helpers (E3.1). Legacy write paths deferred to action engine."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import exists, select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import AppError, inactive_type, not_found
from app.domain.approval import ApprovalTask
from app.domain.audit import HistoryEvent
from app.domain.catalog import RequestType
from app.domain.enums import RoleCode
from app.domain.identity import User
from app.domain.process import Status
from app.domain.request import Request
from app.domain.routing import ApprovalStage
from app.schemas.request import (
    ApprovalTaskSummary,
    CommentOut,
    CreatedComment,
    CreatedRequest,
    FieldValue,
    RequestCard,
    RequestListItem,
    RequestTypeRef,
    StageOut,
    StatusOut,
    UpdatedRequestValues,
    UserRef,
)
from app.services.auth_service import _employee_full_name


def _status_out(status: Status) -> StatusOut:
    return StatusOut(id=status.id, code=status.code, name=status.name)


def _type_ref(request_type: RequestType) -> RequestTypeRef:
    return RequestTypeRef(
        id=request_type.id,
        code=request_type.code,
        name=request_type.name,
    )


def _stage_out(stage: ApprovalStage | None) -> StageOut | None:
    if stage is None:
        return None
    return StageOut(id=stage.id, name=stage.name, sequence_no=stage.sequence_no)


def _clean_request_options() -> tuple:
    from app.domain.audit import Comment

    return (
        selectinload(Request.request_type),
        selectinload(Request.status),
        selectinload(Request.current_stage),
        selectinload(Request.field_values),
        selectinload(Request.approval_tasks),
        selectinload(Request.comments).selectinload(Comment.author).selectinload(User.employee),
        selectinload(Request.initiator).selectinload(User.employee),
    )


def _load_owned_request(session: Session, user: User, request_id: int) -> Request:
    request = session.scalar(
        select(Request)
        .options(*_clean_request_options())
        .where(Request.id == request_id)
    )
    if request is None or request.initiator_user_id != user.id:
        raise not_found()
    return request


def _load_request(session: Session, request_id: int) -> Request:
    request = session.scalar(
        select(Request)
        .options(*_clean_request_options())
        .where(Request.id == request_id)
    )
    if request is None:
        raise not_found()
    return request


def _draft_status(session: Session) -> Status:
    status = session.scalar(select(Status).where(Status.code == "draft"))
    if status is None:
        raise AppError("INTERNAL", "Status draft is not configured", 500)
    return status


def create_draft(session: Session, user: User, request_type_id: int) -> CreatedRequest:
    request_type = session.get(RequestType, request_type_id)
    if request_type is None:
        raise not_found()
    if not request_type.active:
        raise inactive_type()
    draft = _draft_status(session)
    request = Request(
        request_type_id=request_type.id,
        initiator_user_id=user.id,
        status_id=draft.id,
        current_stage_id=None,
    )
    session.add(request)
    session.flush()
    session.add(
        HistoryEvent(
            request_id=request.id,
            actor_id=user.id,
            action="create",
            from_state=None,
            to_state="draft",
            comment=None,
            at=datetime.now(UTC),
        )
    )
    session.commit()
    session.refresh(request)
    request = _load_owned_request(session, user, request.id)
    return CreatedRequest(
        id=request.id,
        request_type_id=request.request_type_id,
        initiator_user_id=request.initiator_user_id,
        status_id=request.status_id,
        status=_status_out(request.status),
        current_stage_id=request.current_stage_id,
        created_at=request.created_at,
        updated_at=request.updated_at,
    )


def list_own_requests(
    session: Session,
    user: User,
    *,
    status: str | None,
    page: int,
    page_size: int,
) -> list[RequestListItem]:
    stmt = (
        select(Request)
        .options(
            selectinload(Request.request_type),
            selectinload(Request.status),
            selectinload(Request.current_stage),
        )
        .where(Request.initiator_user_id == user.id)
        .order_by(Request.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    if status is not None:
        stmt = stmt.join(Request.status).where(Status.code == status)
    rows = session.scalars(stmt).all()
    return [
        RequestListItem(
            id=item.id,
            request_type=_type_ref(item.request_type),
            status=_status_out(item.status),
            current_stage=_stage_out(item.current_stage),
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in rows
    ]


def can_view_request(session: Session, user: User, request: Request) -> bool:
    """BR-01 / BR-14: employee owns request; approver has any ApprovalTask; admin no."""
    if user.role is None:
        return False
    if user.role.code == RoleCode.EMPLOYEE:
        return request.initiator_user_id == user.id
    if user.role.code == RoleCode.APPROVER:
        return bool(
            session.scalar(
                select(
                    exists().where(
                        ApprovalTask.request_id == request.id,
                        ApprovalTask.assignee_user_id == user.id,
                    )
                )
            )
        )
    return False


def get_own_request(session: Session, user: User, request_id: int) -> RequestCard:
    request = _load_owned_request(session, user, request_id)
    return _to_request_card(request)


def get_visible_request_card(session: Session, user: User, request_id: int) -> RequestCard:
    """Request card under BR-01 / BR-14 visibility (AC-ACC-01 / AC-ACC-06)."""
    request = session.scalar(
        select(Request)
        .options(*_clean_request_options())
        .where(Request.id == request_id)
    )
    if request is None or not can_view_request(session, user, request):
        raise not_found()
    return _to_request_card(request)


def get_request_card(session: Session, request_id: int) -> RequestCard:
    """Build Target card by id (Action Engine response; no ownership filter)."""
    request = _load_request(session, request_id)
    return _to_request_card(request)


def _to_request_card(request: Request) -> RequestCard:
    initiator = request.initiator
    return RequestCard(
        id=request.id,
        request_type=_type_ref(request.request_type),
        initiator_user_id=request.initiator_user_id,
        initiator=UserRef(
            id=initiator.id,
            full_name=_employee_full_name(initiator.employee),
        ),
        status_id=request.status_id,
        status=_status_out(request.status),
        current_stage_id=request.current_stage_id,
        current_stage=_stage_out(request.current_stage),
        created_at=request.created_at,
        updated_at=request.updated_at,
        values=[
            FieldValue(field_code=item.field_code, value=item.value)
            for item in sorted(request.field_values, key=lambda row: row.field_code)
        ],
        approval_tasks=[
            ApprovalTaskSummary(
                id=task.id,
                stage_id=task.stage_id,
                assignee_user_id=task.assignee_user_id,
                status=task.status,
                created_at=task.created_at,
                completed_at=task.completed_at,
            )
            for task in request.approval_tasks
        ],
        comments=[
            CommentOut(
                id=comment.id,
                kind=comment.kind,
                text=comment.text,
                author=UserRef(
                    id=comment.author.id,
                    full_name=_employee_full_name(comment.author.employee),
                ),
                approval_task_id=comment.approval_task_id,
                created_at=comment.created_at,
            )
            for comment in sorted(request.comments, key=lambda row: row.created_at)
        ],
    )


def update_working_values(
    session: Session,
    user: User,
    request_id: int,
    values: list[FieldValue],
) -> UpdatedRequestValues:
    raise AppError(
        "INVALID_STATE",
        "Сохранение полей будет доступно после следующего этапа API",
        409,
    )


def cancel_request(session: Session, user: User, request_id: int) -> RequestCard:
    from app.services import submit_service

    return submit_service.cancel_request(session, user, request_id)


def add_free_comment(
    session: Session,
    user: User,
    request_id: int,
    text: str,
) -> CreatedComment:
    raise AppError(
        "INVALID_STATE",
        "Комментарии будут доступны после следующего этапа API",
        409,
    )


# Re-export for available_actions service
load_request_by_id = _load_request
