"""Approval task reads and decision operations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from app.core.errors import (
    forbidden_approval,
    invalid_state,
    task_done,
    validation,
)
from app.domain.approval import ApprovalTask, RouteInstance, RouteInstanceStage
from app.domain.audit import Comment, HistoryEvent
from app.domain.enums import (
    ApprovalDecision,
    ApprovalTaskStatus,
    CommentKind,
    RequestStatus,
)
from app.domain.identity import User
from app.domain.request import Request
from app.schemas.approval import (
    ApprovalRequestCard,
    ApprovalTaskCardResponse,
    ApprovalTaskDetail,
    ApprovalTaskListItem,
    DecisionRequestOut,
    DecisionResult,
    DecisionTaskOut,
)
from app.schemas.request import CommentOut, CurrentStageOut, UserRef
from app.schemas.request_type import RequestTypeRef, RequestTypeSchemaOut
from app.services.request_service import _values_from_document, current_stage_out
from app.services.submit_service import _assignees_for_assignment, _create_stage_tasks

ApprovalAction = Literal["approve", "return", "reject"]
AVAILABLE_ACTIONS: tuple[ApprovalAction, ...] = ("approve", "return", "reject")
HISTORY_APPROVE = "approve"
HISTORY_RETURN = "return"
HISTORY_REJECT = "reject"


def _task_list_options() -> tuple:
    return (
        selectinload(ApprovalTask.request).options(
            selectinload(Request.request_type),
            selectinload(Request.route_instance).selectinload(RouteInstance.stages),
        ),
    )


def _task_card_options() -> tuple:
    return (
        selectinload(ApprovalTask.request).options(
            selectinload(Request.request_type),
            selectinload(Request.initiator),
            selectinload(Request.route_instance).selectinload(RouteInstance.stages),
            selectinload(Request.comments).selectinload(Comment.author),
        ),
        selectinload(ApprovalTask.value_version),
    )


def _stage_out(request: Request, stage_number: int) -> CurrentStageOut:
    instance = request.route_instance
    if instance is not None:
        for stage in instance.stages:
            if stage.sequence_no == stage_number:
                return CurrentStageOut(number=stage.sequence_no, name=stage.name)
    return CurrentStageOut(number=stage_number, name="")


def list_open_tasks(
    session: Session,
    user: User,
    *,
    page: int,
    page_size: int,
) -> list[ApprovalTaskListItem]:
    if page < 1 or page_size < 1 or page_size > 100:
        raise validation({"page": page, "page_size": page_size})

    stmt = (
        select(ApprovalTask)
        .options(*_task_list_options())
        .where(
            ApprovalTask.assignee_id == user.id,
            ApprovalTask.status == ApprovalTaskStatus.OPEN,
        )
        .order_by(ApprovalTask.created_at.asc(), ApprovalTask.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    tasks = session.scalars(stmt).all()

    return [
        ApprovalTaskListItem(
            id=task.id,
            request_id=task.request_id,
            request_type=RequestTypeRef(
                id=task.request.request_type.id,
                name=task.request.request_type.name,
            ),
            stage=_stage_out(task.request, task.stage_number),
            status=ApprovalTaskStatus.OPEN,
            created_at=task.created_at,
        )
        for task in tasks
    ]


def _load_assigned_task(session: Session, user: User, task_id: UUID) -> ApprovalTask:
    task = session.scalar(
        select(ApprovalTask)
        .options(*_task_card_options())
        .where(ApprovalTask.id == task_id)
    )
    if task is None or task.assignee_id != user.id:
        raise forbidden_approval()
    return task


def _comments_out(comments: list[Comment]) -> list[CommentOut]:
    return [
        CommentOut(
            id=comment.id,
            kind=comment.kind,
            text=comment.text,
            author=UserRef(
                id=comment.author.id,
                full_name=comment.author.full_name,
            ),
            approval_task_id=comment.approval_task_id,
            created_at=comment.created_at,
        )
        for comment in comments
    ]


def _available_actions(task: ApprovalTask, request: Request) -> list[ApprovalAction]:
    if (
        task.status != ApprovalTaskStatus.OPEN
        or request.status != RequestStatus.IN_APPROVAL
        or task.stage_number != request.current_stage_number
        or request.initiator_id == task.assignee_id
    ):
        return []
    return list(AVAILABLE_ACTIONS)


def get_task_card(
    session: Session,
    user: User,
    task_id: UUID,
) -> ApprovalTaskCardResponse:
    task = _load_assigned_task(session, user, task_id)
    request = task.request
    version = task.value_version
    if version is None:
        raise RuntimeError("Approval task has no submitted value version")

    stage = current_stage_out(request) or _stage_out(request, task.stage_number)

    return ApprovalTaskCardResponse(
        task=ApprovalTaskDetail(
            id=task.id,
            request_id=task.request_id,
            stage_number=task.stage_number,
            assignee_id=task.assignee_id,
            status=task.status,
            decision=task.decision,
            value_version_id=task.value_version_id,
            decided_at=task.decided_at,
        ),
        request=ApprovalRequestCard(
            id=request.id,
            request_type=RequestTypeRef(
                id=request.request_type.id,
                name=request.request_type.name,
            ),
            initiator=UserRef(
                id=request.initiator.id,
                full_name=request.initiator.full_name,
            ),
            status=request.status,
            current_stage=stage,
            created_at=request.created_at,
            updated_at=request.updated_at,
            form_schema=RequestTypeSchemaOut.model_validate(version.schema_document),
            values=_values_from_document(version.values_document),
            value_source="submitted_version",
            submit_number=version.submit_number,
            comments=_comments_out(request.comments),
        ),
        available_actions=_available_actions(task, request),
    )


def _decision_request_options() -> tuple:
    return (
        selectinload(Request.route_instance)
        .selectinload(RouteInstance.stages)
        .selectinload(RouteInstanceStage.assignments),
    )


def _next_stage(request: Request, stage_number: int) -> RouteInstanceStage | None:
    instance = request.route_instance
    if instance is None:
        raise RuntimeError("Approval request has no route instance")

    stages = sorted(instance.stages, key=lambda item: item.sequence_no)
    for index, stage in enumerate(stages):
        if stage.sequence_no == stage_number:
            return stages[index + 1] if index + 1 < len(stages) else None
    raise invalid_state()


def _load_decision_context(
    session: Session,
    user: User,
    task_id: UUID,
) -> tuple[Request, ApprovalTask]:
    identity = session.execute(
        select(ApprovalTask.request_id, ApprovalTask.assignee_id).where(
            ApprovalTask.id == task_id
        )
    ).one_or_none()
    if identity is None or identity.assignee_id != user.id:
        raise forbidden_approval()

    request = session.scalar(
        select(Request)
        .options(*_decision_request_options())
        .where(Request.id == identity.request_id)
        .with_for_update()
    )
    if request is None:
        raise RuntimeError("Approval task references a missing request")

    task = session.scalar(
        select(ApprovalTask).where(ApprovalTask.id == task_id).with_for_update()
    )
    if task is None or task.assignee_id != user.id:
        raise forbidden_approval()
    if task.status != ApprovalTaskStatus.OPEN:
        raise task_done()
    if request.initiator_id == user.id:
        raise forbidden_approval()
    if (
        request.status != RequestStatus.IN_APPROVAL
        or task.stage_number != request.current_stage_number
    ):
        raise invalid_state()
    if task.value_version_id is None:
        raise RuntimeError("Approval task has no submitted value version")
    return request, task


def _claim_task_decision(
    session: Session,
    user: User,
    task: ApprovalTask,
    decision: ApprovalDecision,
) -> None:
    decided_at = datetime.now(timezone.utc)
    claimed = session.execute(
        update(ApprovalTask)
        .where(
            ApprovalTask.id == task.id,
            ApprovalTask.assignee_id == user.id,
            ApprovalTask.status == ApprovalTaskStatus.OPEN,
        )
        .values(
            status=ApprovalTaskStatus.COMPLETED,
            decision=decision,
            decided_at=decided_at,
        )
        .execution_options(synchronize_session=False)
    )
    if claimed.rowcount != 1:
        raise task_done()


def _cancel_sibling_tasks(
    session: Session,
    request: Request,
    task: ApprovalTask,
) -> None:
    session.execute(
        update(ApprovalTask)
        .where(
            ApprovalTask.request_id == request.id,
            ApprovalTask.stage_number == task.stage_number,
            ApprovalTask.id != task.id,
            ApprovalTask.status == ApprovalTaskStatus.OPEN,
        )
        .values(status=ApprovalTaskStatus.CANCELLED)
        .execution_options(synchronize_session=False)
    )


def _add_decision_comment(
    session: Session,
    user: User,
    request: Request,
    task: ApprovalTask,
    comment: str,
) -> None:
    if not comment:
        return
    session.add(
        Comment(
            request_id=request.id,
            author_id=user.id,
            approval_task_id=task.id,
            kind=CommentKind.DECISION,
            text=comment,
        )
    )


def _add_decision_history(
    session: Session,
    user: User,
    request: Request,
    *,
    action: str,
    comment: str,
) -> None:
    session.add(
        HistoryEvent(
            request_id=request.id,
            actor_id=user.id,
            action=action,
            from_state=RequestStatus.IN_APPROVAL.value,
            to_state=request.status.value,
            comment=comment or None,
        )
    )


def _decision_result(
    request: Request,
    task: ApprovalTask,
    decision: ApprovalDecision,
) -> DecisionResult:
    if task.value_version_id is None:
        raise RuntimeError("Approval task has no submitted value version")
    current_stage = current_stage_out(request) or _stage_out(request, task.stage_number)
    return DecisionResult(
        task=DecisionTaskOut(
            id=task.id,
            status=ApprovalTaskStatus.COMPLETED,
            decision=decision,
            value_version_id=task.value_version_id,
        ),
        request=DecisionRequestOut(
            id=request.id,
            status=request.status,
            current_stage=current_stage,
        ),
    )


def _required_decision_comment(comment: object) -> str:
    if not isinstance(comment, str):
        raise validation({"comment": "required"})
    normalized = comment.strip()
    if not normalized:
        raise validation({"comment": "required"})
    return normalized


def _terminal_decision(
    session: Session,
    user: User,
    task_id: UUID,
    comment: object,
    *,
    decision: ApprovalDecision,
    request_status: RequestStatus,
    history_action: str,
) -> DecisionResult:
    normalized_comment = _required_decision_comment(comment)
    request, task = _load_decision_context(session, user, task_id)

    _claim_task_decision(session, user, task, decision)
    _cancel_sibling_tasks(session, request, task)
    request.status = request_status

    _add_decision_comment(
        session,
        user,
        request,
        task,
        normalized_comment,
    )
    _add_decision_history(
        session,
        user,
        request,
        action=history_action,
        comment=normalized_comment,
    )
    session.flush()

    return _decision_result(request, task, decision)


def approve_task(
    session: Session,
    user: User,
    task_id: UUID,
    comment: str | None,
) -> DecisionResult:
    request, task = _load_decision_context(session, user, task_id)

    next_stage = _next_stage(request, task.stage_number)
    next_assignee_ids: set[UUID] = set()
    if next_stage is not None:
        for assignment in next_stage.assignments:
            next_assignee_ids.update(_assignees_for_assignment(session, assignment))
        if not next_assignee_ids:
            raise RuntimeError("Next approval stage has no active assignees")

    _claim_task_decision(session, user, task, ApprovalDecision.APPROVE)
    _cancel_sibling_tasks(session, request, task)

    if next_stage is None:
        request.status = RequestStatus.APPROVED
    else:
        request.current_stage_number = next_stage.sequence_no
        _create_stage_tasks(
            session,
            request,
            stage_number=next_stage.sequence_no,
            assignee_ids=list(next_assignee_ids),
            value_version_id=task.value_version_id,
        )

    normalized_comment = comment.strip() if comment is not None else ""
    _add_decision_comment(
        session,
        user,
        request,
        task,
        normalized_comment,
    )
    _add_decision_history(
        session,
        user,
        request,
        action=HISTORY_APPROVE,
        comment=normalized_comment,
    )
    session.flush()

    return _decision_result(request, task, ApprovalDecision.APPROVE)


def return_task(
    session: Session,
    user: User,
    task_id: UUID,
    comment: str | None,
) -> DecisionResult:
    return _terminal_decision(
        session,
        user,
        task_id,
        comment,
        decision=ApprovalDecision.RETURN,
        request_status=RequestStatus.RETURNED,
        history_action=HISTORY_RETURN,
    )


def reject_task(
    session: Session,
    user: User,
    task_id: UUID,
    comment: str | None,
) -> DecisionResult:
    return _terminal_decision(
        session,
        user,
        task_id,
        comment,
        decision=ApprovalDecision.REJECT,
        request_status=RequestStatus.REJECTED,
        history_action=HISTORY_REJECT,
    )
