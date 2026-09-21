"""Submit orchestrator: validate, snapshot route/values, create stage-1 tasks."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import inactive_type, invalid_state, route_config, validation
from app.domain.approval import (
    ApprovalTask,
    RouteInstance,
    RouteInstanceAssignment,
    RouteInstanceStage,
)
from app.domain.audit import HistoryEvent
from app.domain.enums import ApprovalTaskStatus, AssignmentKind, RequestStatus
from app.domain.identity import User, UserRole
from app.domain.request import FieldValueVersion, Request
from app.domain.routing import ApprovalRoute, ApprovalStage, StageAssignment
from app.schemas.request import CurrentStageOut, FieldValue, SubmitRequestResult
from app.services.field_validation import definitions_by_code, validate_field_value
from app.services.request_service import current_stage_out, load_owned_request
from app.services.schema_mapping import to_type_schema

HISTORY_SUBMIT = "submit"
SUBMITTABLE_STATUSES = {RequestStatus.DRAFT, RequestStatus.RETURNED}


def _validate_live_route(route: ApprovalRoute | None) -> list[ApprovalStage]:
    if route is None or not route.stages:
        raise route_config()
    stages = sorted(route.stages, key=lambda item: item.sequence_no)
    for stage in stages:
        if not stage.assignments:
            raise route_config()
    return stages


def _working_map(request: Request) -> dict[str, str | None]:
    return {item.field_code: item.value for item in request.field_values}


def _validate_required_values(session: Session, request: Request) -> list[FieldValue]:
    fields = sorted(request.request_type.field_definitions, key=lambda item: item.order_no)
    by_code = definitions_by_code(fields)
    working = _working_map(request)
    validated: list[FieldValue] = []
    missing: list[str] = []

    for field in fields:
        raw = working.get(field.code)
        canonical = validate_field_value(session, field, raw)
        if field.required and canonical is None:
            missing.append(field.code)
        validated.append(FieldValue(field_code=field.code, value=canonical))

    extra_codes = set(working) - set(by_code)
    if extra_codes:
        raise validation({"unknown_fields": sorted(extra_codes)})
    if missing:
        raise validation({"missing_required": missing})
    return validated


def _copy_route_instance(session: Session, request: Request, stages: list[ApprovalStage]) -> RouteInstance:
    instance = RouteInstance(request_id=request.id)
    session.add(instance)
    session.flush()
    for stage in stages:
        instance_stage = RouteInstanceStage(
            route_instance_id=instance.id,
            name=stage.name,
            sequence_no=stage.sequence_no,
        )
        session.add(instance_stage)
        session.flush()
        for assignment in stage.assignments:
            session.add(
                RouteInstanceAssignment(
                    instance_stage_id=instance_stage.id,
                    assignment_kind=assignment.assignment_kind,
                    role_id=assignment.role_id,
                    user_id=assignment.user_id,
                )
            )
    session.flush()
    return instance


def _assignees_for_assignment(session: Session, assignment: StageAssignment | RouteInstanceAssignment) -> list[UUID]:
    user_ids: set[UUID] = set()
    if assignment.assignment_kind == AssignmentKind.ROLE and assignment.role_id is not None:
        rows = session.scalars(
            select(User.id).join(UserRole).where(
                UserRole.role_id == assignment.role_id,
                User.is_active.is_(True),
            )
        )
        user_ids.update(rows)
    if assignment.user_id is not None and assignment.assignment_kind in {
        AssignmentKind.USER,
        AssignmentKind.ROLE_AND_USER,
    }:
        user_ids.add(assignment.user_id)
    return list(user_ids)


def _first_stage_assignments(
    session: Session,
    request: Request,
    live_stages: list[ApprovalStage],
) -> tuple[int, str, list[UUID]]:
    if request.route_instance is not None and request.route_instance.stages:
        stages = sorted(request.route_instance.stages, key=lambda item: item.sequence_no)
        first = stages[0]
        assignee_ids: set[UUID] = set()
        for assignment in first.assignments:
            assignee_ids.update(_assignees_for_assignment(session, assignment))
        return first.sequence_no, first.name, list(assignee_ids)

    first = live_stages[0]
    assignee_ids = set()
    for assignment in first.assignments:
        assignee_ids.update(_assignees_for_assignment(session, assignment))
    return first.sequence_no, first.name, list(assignee_ids)


def _create_stage_tasks(
    session: Session,
    request: Request,
    *,
    stage_number: int,
    assignee_ids: list[UUID],
    value_version_id: UUID,
) -> None:
    created_at = datetime.now(timezone.utc)
    for assignee_id in assignee_ids:
        session.add(
            ApprovalTask(
                request_id=request.id,
                stage_number=stage_number,
                assignee_id=assignee_id,
                status=ApprovalTaskStatus.OPEN,
                decision=None,
                value_version_id=value_version_id,
                created_at=created_at,
            )
        )


def submit_request(session: Session, user: User, request_id: UUID) -> SubmitRequestResult:
    request = load_owned_request(session, request_id, user)
    if request.status not in SUBMITTABLE_STATUSES:
        raise invalid_state()
    if not request.request_type.is_active:
        raise inactive_type()

    route = session.scalar(
        select(ApprovalRoute)
        .options(
            selectinload(ApprovalRoute.stages).selectinload(ApprovalStage.assignments),
        )
        .where(ApprovalRoute.request_type_id == request.request_type_id)
    )
    live_stages = _validate_live_route(route)
    values = _validate_required_values(session, request)

    first_submit = request.route_instance is None
    if first_submit:
        request.route_instance = _copy_route_instance(session, request, live_stages)

    previous_number = max((item.submit_number for item in request.field_value_versions), default=0)
    submit_number = previous_number + 1
    schema_document = to_type_schema(request.request_type).model_dump(mode="json")
    values_document = [item.model_dump(mode="json") for item in values]
    version = FieldValueVersion(
        request_id=request.id,
        submit_number=submit_number,
        schema_document=schema_document,
        values_document=values_document,
    )
    session.add(version)
    session.flush()

    if first_submit:
        first = live_stages[0]
        assignee_ids: set[UUID] = set()
        for assignment in first.assignments:
            assignee_ids.update(_assignees_for_assignment(session, assignment))
        stage_number, stage_name = first.sequence_no, first.name
    else:
        stage_number, stage_name, assignee_list = _first_stage_assignments(
            session, request, live_stages
        )
        assignee_ids = set(assignee_list)

    _create_stage_tasks(
        session,
        request,
        stage_number=stage_number,
        assignee_ids=list(assignee_ids),
        value_version_id=version.id,
    )

    from_state = request.status.value
    request.status = RequestStatus.IN_APPROVAL
    request.current_stage_number = stage_number
    session.add(
        HistoryEvent(
            request_id=request.id,
            actor_id=user.id,
            action=HISTORY_SUBMIT,
            from_state=from_state,
            to_state=RequestStatus.IN_APPROVAL.value,
        )
    )
    session.flush()
    session.refresh(request)

    stage = current_stage_out(request) or CurrentStageOut(number=stage_number, name=stage_name)

    return SubmitRequestResult(
        id=request.id,
        status=RequestStatus.IN_APPROVAL,
        current_stage=stage,
        submit_number=submit_number,
        updated_at=request.updated_at,
    )
