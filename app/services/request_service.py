"""Create, list, read, and edit employee requests (draft/returned)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import inactive_type, invalid_state, not_found, validation
from app.domain.approval import RouteInstance, RouteInstanceStage
from app.domain.audit import HistoryEvent
from app.domain.catalog import Dictionary, RequestFieldDefinition, RequestType
from app.domain.enums import RequestStatus
from app.domain.identity import User
from app.domain.request import FieldValueVersion, Request, RequestFieldValue
from app.schemas.request import (
    CreatedRequest,
    CurrentStageOut,
    FieldValue,
    RequestCard,
    RequestListItem,
    UpdatedRequestValues,
    UserRef,
)
from app.schemas.request_type import RequestTypeRef, RequestTypeSchemaOut
from app.services.field_validation import definitions_by_code, validate_field_value
from app.services.schema_mapping import to_type_schema

HISTORY_CREATED = "created"

EDITABLE_STATUSES = {RequestStatus.DRAFT, RequestStatus.RETURNED}
SNAPSHOT_STATUSES = {
    RequestStatus.IN_APPROVAL,
    RequestStatus.APPROVED,
    RequestStatus.REJECTED,
}


def _type_options() -> tuple:
    return (
        selectinload(RequestType.field_definitions)
        .selectinload(RequestFieldDefinition.dictionary)
        .selectinload(Dictionary.items),
        selectinload(RequestType.approval_route),
    )


def _request_card_options() -> tuple:
    return (
        selectinload(Request.request_type).options(*_type_options()),
        selectinload(Request.initiator),
        selectinload(Request.field_values),
        selectinload(Request.field_value_versions),
        selectinload(Request.route_instance)
        .selectinload(RouteInstance.stages)
        .selectinload(RouteInstanceStage.assignments),
    )


def _request_list_options() -> tuple:
    return (
        selectinload(Request.request_type),
        selectinload(Request.route_instance).selectinload(RouteInstance.stages),
    )


def current_stage_out(request: Request) -> CurrentStageOut | None:
    if request.current_stage_number is None:
        return None
    instance = request.route_instance
    if instance is not None:
        for stage in instance.stages:
            if stage.sequence_no == request.current_stage_number:
                return CurrentStageOut(number=stage.sequence_no, name=stage.name)
    return CurrentStageOut(number=request.current_stage_number, name="")


def load_owned_request(session: Session, request_id: UUID, user: User) -> Request:
    request = session.scalar(
        select(Request).options(*_request_card_options()).where(Request.id == request_id)
    )
    if request is None or request.initiator_id != user.id:
        raise not_found()
    return request


def create_draft(session: Session, user: User, request_type_id: UUID) -> CreatedRequest:
    request_type = session.get(RequestType, request_type_id)
    if request_type is None:
        raise not_found()
    if not request_type.is_active:
        raise inactive_type()

    request = Request(
        initiator_id=user.id,
        request_type_id=request_type.id,
        status=RequestStatus.DRAFT,
        current_stage_number=None,
    )
    session.add(request)
    session.flush()
    session.add(
        HistoryEvent(
            request_id=request.id,
            actor_id=user.id,
            action=HISTORY_CREATED,
            from_state=None,
            to_state=RequestStatus.DRAFT.value,
        )
    )
    session.flush()
    return CreatedRequest(
        id=request.id,
        request_type_id=request.request_type_id,
        initiator_id=request.initiator_id,
        status=RequestStatus.DRAFT,
        current_stage_number=request.current_stage_number,
        created_at=request.created_at,
        updated_at=request.updated_at,
    )


def list_own_requests(
    session: Session,
    user: User,
    *,
    status: RequestStatus | None,
    page: int,
    page_size: int,
) -> list[RequestListItem]:
    if page < 1 or page_size < 1 or page_size > 100:
        raise validation({"page": page, "page_size": page_size})

    stmt = (
        select(Request)
        .options(*_request_list_options())
        .where(Request.initiator_id == user.id)
    )
    if status is not None:
        stmt = stmt.where(Request.status == status)
    stmt = (
        stmt.order_by(Request.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = session.scalars(stmt).all()
    return [
        RequestListItem(
            id=item.id,
            request_type=RequestTypeRef(id=item.request_type.id, name=item.request_type.name),
            status=item.status,
            current_stage=current_stage_out(item),
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in rows
    ]


def _working_values(request: Request) -> list[FieldValue]:
    return [
        FieldValue(field_code=item.field_code, value=item.value)
        for item in sorted(request.field_values, key=lambda row: row.field_code)
    ]


def _latest_version(request: Request) -> FieldValueVersion | None:
    if not request.field_value_versions:
        return None
    return max(request.field_value_versions, key=lambda item: item.submit_number)


def _values_from_document(document: object) -> list[FieldValue]:
    if isinstance(document, list):
        return [FieldValue.model_validate(item) for item in document]
    if isinstance(document, dict) and "values" in document:
        return [FieldValue.model_validate(item) for item in document["values"]]
    return []


def get_own_request(session: Session, user: User, request_id: UUID) -> RequestCard:
    request = load_owned_request(session, request_id, user)
    live_schema = to_type_schema(request.request_type)
    latest = _latest_version(request)

    if request.status in SNAPSHOT_STATUSES and latest is not None:
        form_schema = RequestTypeSchemaOut.model_validate(latest.schema_document)
        values = _values_from_document(latest.values_document)
        value_source: str = "submitted_version"
        submit_number = latest.submit_number
    else:
        form_schema = live_schema
        values = _working_values(request)
        value_source = "working"
        submit_number = latest.submit_number if latest is not None else None

    return RequestCard(
        id=request.id,
        request_type=RequestTypeRef(id=request.request_type.id, name=request.request_type.name),
        initiator=UserRef(id=request.initiator.id, full_name=request.initiator.full_name),
        status=request.status,
        current_stage=current_stage_out(request),
        created_at=request.created_at,
        updated_at=request.updated_at,
        form_schema=form_schema,
        values=values,
        value_source=value_source,  # type: ignore[arg-type]
        submit_number=submit_number,
        comments=[],
    )


def update_working_values(
    session: Session,
    user: User,
    request_id: UUID,
    values: list[FieldValue],
) -> UpdatedRequestValues:
    request = load_owned_request(session, request_id, user)
    if request.status not in EDITABLE_STATUSES:
        raise invalid_state()

    fields = definitions_by_code(list(request.request_type.field_definitions))
    existing = {item.field_code: item for item in request.field_values}

    for item in values:
        field = fields.get(item.field_code)
        if field is None:
            raise validation({"field_code": item.field_code, "reason": "unknown_field"})
        canonical = validate_field_value(session, field, item.value)
        row = existing.get(item.field_code)
        if row is None:
            row = RequestFieldValue(request_id=request.id, field_code=item.field_code, value=canonical)
            session.add(row)
            existing[item.field_code] = row
        else:
            row.value = canonical

    session.flush()
    session.refresh(request)
    return UpdatedRequestValues(
        id=request.id,
        status=request.status,
        form_schema=to_type_schema(request.request_type),
        values=_working_values(request),
        updated_at=request.updated_at,
    )
