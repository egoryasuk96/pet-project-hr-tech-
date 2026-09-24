"""Target Action Engine: execute ProcessTransition effects (E3.2 / ADR-ACTION-01).

Permission comes only from live ProcessTransition rows — not a Python matrix.
Side effects use transition.effect and to_status codes (not a hardcoded allow-list).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import (
    AppError,
    action_not_allowed,
    action_not_found,
    approval_task_not_found,
    comment_required,
    invalid_request_state,
    request_not_found,
    route_config,
    self_approval_forbidden,
    task_done,
)
from app.domain.approval import ApprovalTask
from app.domain.audit import Comment, HistoryEvent
from app.domain.catalog import RequestType
from app.domain.enums import (
    ApprovalTaskStatus,
    AssignmentKind,
    CommentKind,
    ProcessTransitionEffect,
    RoleCode,
)
from app.domain.identity import User
from app.domain.process import Action, ProcessTransition, Status
from app.domain.request import Request
from app.domain.routing import ApprovalRoute, ApprovalStage, StageAssignment
from app.schemas.request import RequestCard
from app.services import notification_service, request_service
from app.services.notification_service import ActionOutcome


def _before_commit_hook(session: Session) -> None:
    """No-op extension point; tests may monkeypatch to force rollback."""


def execute_action(
    session: Session,
    user: User,
    request_id: int,
    action_id: int,
    comment: str | None = None,
) -> RequestCard:
    """Apply one configured action to a request inside the current DB transaction."""
    request = _lock_request(session, request_id)
    _assert_employee_owns_request(user, request)

    action = session.get(Action, action_id)
    if action is None or not action.active:
        raise action_not_found()

    request_type = session.scalar(
        select(RequestType)
        .options(selectinload(RequestType.approval_route).selectinload(ApprovalRoute.stages))
        .where(RequestType.id == request.request_type_id)
    )
    if request_type is None:
        raise invalid_request_state()

    transition = _find_transition(
        session,
        process_id=request_type.process_id,
        from_status_id=request.status_id,
        action_id=action.id,
        role_id=user.role_id,
    )
    if transition is None:
        if action.code in {"approve", "reject", "return"} and _user_has_closed_task(
            session, request, user
        ):
            raise task_done()
        raise action_not_allowed()

    to_status = session.get(Status, transition.to_status_id)
    if to_status is None:
        raise AppError("INTERNAL", "Целевой статус перехода не найден", 500)

    from_status = session.get(Status, request.status_id)
    if from_status is None:
        raise AppError("INTERNAL", "Текущий статус заявки не найден", 500)
    from_state = from_status.code

    if transition.effect == ProcessTransitionEffect.APPROVE_ADVANCE:
        outcome = _apply_approve_advance(session, user, request, transition, to_status)
    elif transition.effect == ProcessTransitionEffect.STATUS_ONLY:
        outcome = _apply_status_only(
            session, user, request, request_type, transition, to_status, comment
        )
    else:
        raise AppError("INTERNAL", f"Неизвестный effect: {transition.effect}", 500)

    final_status = session.get(Status, request.status_id)
    if final_status is None:
        raise AppError("INTERNAL", "Итоговый статус заявки не найден", 500)

    history_comment: str | None = None
    if action.code in {"reject", "return"} and comment is not None:
        history_comment = comment.strip() or None

    session.add(
        HistoryEvent(
            request_id=request.id,
            actor_id=user.id,
            action=action.code,
            from_state=from_state,
            to_state=final_status.code,
            comment=history_comment,
            at=datetime.now(UTC),
        )
    )
    notification_service.create_notifications_for_action(
        session,
        request=request,
        action_code=action.code,
        outcome=outcome,
    )
    session.flush()
    _before_commit_hook(session)
    session.commit()
    return request_service.get_request_card(session, request.id)


def _lock_request(session: Session, request_id: int) -> Request:
    request = session.scalar(
        select(Request).where(Request.id == request_id).with_for_update()
    )
    if request is None:
        raise request_not_found()
    return request


def _assert_employee_owns_request(user: User, request: Request) -> None:
    if user.role is not None and user.role.code == RoleCode.EMPLOYEE:
        if request.initiator_user_id != user.id:
            raise request_not_found()


def _find_transition(
    session: Session,
    *,
    process_id: int,
    from_status_id: int,
    action_id: int,
    role_id: int,
) -> ProcessTransition | None:
    return session.scalar(
        select(ProcessTransition)
        .options(
            selectinload(ProcessTransition.action),
            selectinload(ProcessTransition.to_status),
            selectinload(ProcessTransition.from_status),
        )
        .where(
            ProcessTransition.process_id == process_id,
            ProcessTransition.from_status_id == from_status_id,
            ProcessTransition.action_id == action_id,
            ProcessTransition.role_id == role_id,
            ProcessTransition.is_active.is_(True),
        )
        .order_by(ProcessTransition.sort_order, ProcessTransition.id)
        .limit(1)
    )


def _apply_status_only(
    session: Session,
    user: User,
    request: Request,
    request_type: RequestType,
    transition: ProcessTransition,
    to_status: Status,
    comment: str | None,
) -> ActionOutcome:
    to_code = to_status.code

    if to_code in {"rejected", "returned"}:
        _assert_not_self_approval(request, user)
        _require_comment(comment)
        task = _require_open_task(session, request, user)
        decision_text = comment.strip()
        _complete_task(task, comment=decision_text)
        _cancel_sibling_open_tasks(session, request, task)
        session.add(
            Comment(
                request_id=request.id,
                author_id=user.id,
                approval_task_id=task.id,
                kind=CommentKind.DECISION,
                text=decision_text,
                created_at=datetime.now(UTC),
            )
        )
        request.status_id = transition.to_status_id
        # Keep current_stage_id for audit (BR-05 / Target contract).
        return ActionOutcome(closed_task=task)

    if to_code == "cancelled":
        request.status_id = transition.to_status_id
        request.current_stage_id = None
        return ActionOutcome()

    if to_code == "in_approval":
        from app.services.field_validation import validate_submit

        validate_submit(session, request, request_type)
        request.status_id = transition.to_status_id
        first_stage = _first_stage(session, request_type)
        request.current_stage_id = first_stage.id
        created = _create_tasks_for_stage(session, request, first_stage)
        return ActionOutcome(created_tasks=created)

    # Generic status_only fallback
    request.status_id = transition.to_status_id
    request.current_stage_id = None
    return ActionOutcome()


def _apply_approve_advance(
    session: Session,
    user: User,
    request: Request,
    transition: ProcessTransition,
    to_status: Status,
) -> ActionOutcome:
    _assert_not_self_approval(request, user)

    task = _require_open_task(session, request, user)
    _complete_task(task, comment=None)
    _cancel_sibling_open_tasks(session, request, task)

    next_stage = _next_stage(session, request, task.stage_id)
    if next_stage is None:
        request.status_id = transition.to_status_id
        request.current_stage_id = None
        return ActionOutcome(closed_task=task)

    request.current_stage_id = next_stage.id
    # Stay in approval while advancing; to_status applies only on final stage.
    in_approval = session.scalar(select(Status).where(Status.code == "in_approval"))
    if in_approval is None:
        raise AppError("INTERNAL", "Status in_approval is not configured", 500)
    request.status_id = in_approval.id
    created = _create_tasks_for_stage(session, request, next_stage)
    return ActionOutcome(closed_task=task, created_tasks=created)


def _assert_not_self_approval(request: Request, user: User) -> None:
    """BR-21: initiator cannot approve / reject / return own request."""
    if request.initiator_user_id == user.id:
        raise self_approval_forbidden()


def _cancel_sibling_open_tasks(
    session: Session,
    request: Request,
    task: ApprovalTask,
) -> None:
    """Cancel remaining open tasks on the same stage (actor task already completed)."""
    siblings = session.scalars(
        select(ApprovalTask).where(
            ApprovalTask.request_id == request.id,
            ApprovalTask.stage_id == task.stage_id,
            ApprovalTask.status == ApprovalTaskStatus.OPEN,
            ApprovalTask.id != task.id,
        )
    ).all()
    now = datetime.now(UTC)
    for sibling in siblings:
        sibling.status = ApprovalTaskStatus.CANCELLED
        sibling.completed_at = now


def _require_comment(comment: str | None) -> None:
    if comment is None or not comment.strip():
        raise comment_required()


def _require_open_task(session: Session, request: Request, user: User) -> ApprovalTask:
    if request.current_stage_id is not None:
        task = session.scalar(
            select(ApprovalTask)
            .where(
                ApprovalTask.request_id == request.id,
                ApprovalTask.stage_id == request.current_stage_id,
                ApprovalTask.assignee_user_id == user.id,
                ApprovalTask.status == ApprovalTaskStatus.OPEN,
            )
            .order_by(ApprovalTask.id)
            .limit(1)
        )
        if task is not None:
            return task
        if _user_has_closed_task(session, request, user, stage_id=request.current_stage_id):
            raise task_done()
        raise approval_task_not_found()

    if _user_has_closed_task(session, request, user):
        raise task_done()
    raise approval_task_not_found()


def _user_has_closed_task(
    session: Session,
    request: Request,
    user: User,
    *,
    stage_id: int | None = None,
) -> bool:
    """True if user has completed/cancelled ApprovalTask on the request (optionally stage)."""
    stmt = select(ApprovalTask.id).where(
        ApprovalTask.request_id == request.id,
        ApprovalTask.assignee_user_id == user.id,
        ApprovalTask.status.in_(
            (ApprovalTaskStatus.COMPLETED, ApprovalTaskStatus.CANCELLED)
        ),
    )
    if stage_id is not None:
        stmt = stmt.where(ApprovalTask.stage_id == stage_id)
    return session.scalar(stmt.limit(1)) is not None


def _complete_task(task: ApprovalTask, *, comment: str | None) -> None:
    task.status = ApprovalTaskStatus.COMPLETED
    task.completed_at = datetime.now(UTC)
    if comment is not None:
        task.comment = comment


def _first_stage(session: Session, request_type: RequestType) -> ApprovalStage:
    route = session.scalar(
        select(ApprovalRoute)
        .options(
            selectinload(ApprovalRoute.stages).selectinload(ApprovalStage.assignments)
        )
        .where(ApprovalRoute.request_type_id == request_type.id)
    )
    if route is None or not route.stages:
        raise route_config()
    stages = sorted(route.stages, key=lambda item: item.sequence_no)
    return stages[0]


def _next_stage(
    session: Session,
    request: Request,
    current_stage_id: int,
) -> ApprovalStage | None:
    current = session.get(ApprovalStage, current_stage_id)
    if current is None:
        raise invalid_request_state()
    return session.scalar(
        select(ApprovalStage)
        .options(selectinload(ApprovalStage.assignments))
        .where(
            ApprovalStage.route_id == current.route_id,
            ApprovalStage.sequence_no > current.sequence_no,
        )
        .order_by(ApprovalStage.sequence_no)
        .limit(1)
    )


def _create_tasks_for_stage(
    session: Session,
    request: Request,
    stage: ApprovalStage,
) -> list[ApprovalTask]:
    assignments = list(stage.assignments)
    if not assignments:
        # Reload assignments if stage came without them
        assignments = list(
            session.scalars(
                select(StageAssignment).where(StageAssignment.stage_id == stage.id)
            ).all()
        )
    if not assignments:
        raise route_config()

    assignee_ids = _resolve_assignee_user_ids(session, assignments)
    if not assignee_ids:
        raise route_config()

    created: list[ApprovalTask] = []
    for user_id in assignee_ids:
        task = ApprovalTask(
            request_id=request.id,
            stage_id=stage.id,
            assignee_user_id=user_id,
            status=ApprovalTaskStatus.OPEN,
        )
        session.add(task)
        created.append(task)
    session.flush()
    return created


def _resolve_assignee_user_ids(
    session: Session,
    assignments: list[StageAssignment],
) -> list[uuid.UUID]:
    resolved: list[uuid.UUID] = []
    seen: set[uuid.UUID] = set()

    for assignment in assignments:
        candidates: list[uuid.UUID] = []
        if assignment.assignment_kind == AssignmentKind.USER:
            if assignment.user_id is not None:
                candidates.append(assignment.user_id)
        elif assignment.assignment_kind == AssignmentKind.ROLE:
            if assignment.role_id is not None:
                users = session.scalars(
                    select(User).where(
                        User.role_id == assignment.role_id,
                        User.is_active.is_(True),
                    )
                ).all()
                candidates.extend(user.id for user in users)
        elif assignment.assignment_kind == AssignmentKind.ROLE_AND_USER:
            if assignment.user_id is not None:
                candidates.append(assignment.user_id)

        for user_id in candidates:
            if user_id not in seen:
                seen.add(user_id)
                resolved.append(user_id)

    return resolved


def action_id_by_code(session: Session, code: str) -> int:
    action = session.scalar(select(Action).where(Action.code == code, Action.active.is_(True)))
    if action is None:
        raise action_not_found()
    return action.id
