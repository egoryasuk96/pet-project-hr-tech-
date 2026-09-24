"""P0 / AC-APP-05: multi-stage approve_advance via Target Action Engine.

Proves live ProcessTransition(effect=approve_advance) advances stage 1 → stage 2,
then final approve completes the request — without duplicating workflow logic in the test.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.security import hash_password
from app.db.session import get_session_factory
from app.domain.approval import ApprovalTask
from app.domain.audit import HistoryEvent
from app.domain.catalog import RequestFieldDefinition, RequestType
from app.domain.enums import (
    ApprovalTaskStatus,
    AssignmentKind,
    FieldDataType,
    NotificationEventType,
    ProcessTransitionEffect,
    RoleCode,
)
from app.domain.identity import Role, User
from app.domain.notification import Notification
from app.domain.org import Company, Department, Employee
from app.domain.process import Action, Process, ProcessTransition, Status
from app.domain.routing import ApprovalRoute, ApprovalStage, StageAssignment
from tests.conftest import TEST_PASSWORD, ApiDataset, auth_header, fill_valid_vacation_fields


APPROVER2_LOGIN = "approver2.multistage"


@dataclass(frozen=True)
class MultiStageSetup:
    type_id: int
    stage1_id: int
    stage2_id: int
    approver1_login: str
    approver2_login: str
    approve_action_id: int
    submit_action_id: int
    transition_effect: ProcessTransitionEffect


def _execute(
    client: TestClient,
    headers: dict[str, str],
    request_id: int,
    action_id: int,
    comment: str | None = None,
):
    body: dict = {}
    if comment is not None:
        body["comment"] = comment
    return client.post(
        f"/requests/{request_id}/actions/{action_id}",
        headers=headers,
        json=body,
    )


def _user_id(login: str) -> UUID:
    session = get_session_factory()()
    try:
        user = session.scalar(select(User).where(User.login == login))
        assert user is not None
        return user.id
    finally:
        session.close()


def _tasks(request_id: int) -> list[ApprovalTask]:
    session = get_session_factory()()
    try:
        return list(
            session.scalars(
                select(ApprovalTask)
                .where(ApprovalTask.request_id == request_id)
                .order_by(ApprovalTask.id)
            ).all()
        )
    finally:
        session.close()


def _history(request_id: int) -> list[HistoryEvent]:
    session = get_session_factory()()
    try:
        return list(
            session.scalars(
                select(HistoryEvent)
                .where(HistoryEvent.request_id == request_id)
                .order_by(HistoryEvent.id)
            ).all()
        )
    finally:
        session.close()


def _notifications(request_id: int) -> list[Notification]:
    session = get_session_factory()()
    try:
        return list(
            session.scalars(
                select(Notification)
                .where(Notification.request_id == request_id)
                .order_by(Notification.id)
            ).all()
        )
    finally:
        session.close()


def _ensure_approver2(session) -> User:
    """Test-only second approver (not production seed)."""
    existing = session.scalar(select(User).where(User.login == APPROVER2_LOGIN))
    if existing is not None:
        return existing

    role = session.scalar(select(Role).where(Role.code == RoleCode.APPROVER))
    assert role is not None
    company = session.scalar(select(Company).limit(1))
    assert company is not None
    department = session.scalar(
        select(Department).where(Department.company_id == company.id).limit(1)
    )
    assert department is not None

    employee = Employee(
        employee_number="EMP-approver2.multistage",
        first_name="Пётр",
        last_name="Второй",
        department_id=department.id,
        position="Согласующий 2",
        active=True,
    )
    session.add(employee)
    session.flush()

    user = User(
        login=APPROVER2_LOGIN,
        password_hash=hash_password(TEST_PASSWORD),
        is_active=True,
        role_id=role.id,
        employee_id=employee.id,
    )
    session.add(user)
    session.flush()
    return user


def _configure_two_stage_vacation_route(
    dataset: ApiDataset,
) -> MultiStageSetup:
    """Attach stage 2 to vacation live route; keep existing ProcessTransition matrix."""
    session = get_session_factory()()
    try:
        process = session.scalar(select(Process).where(Process.code == "employee_requests"))
        assert process is not None

        approve = session.get(Action, dataset.approve_action_id)
        in_approval = session.get(Status, dataset.in_approval_status_id)
        approved = session.scalar(select(Status).where(Status.code == "approved"))
        approver_role = session.scalar(select(Role).where(Role.code == RoleCode.APPROVER))
        assert approve and in_approval and approved and approver_role

        transition = session.scalar(
            select(ProcessTransition).where(
                ProcessTransition.process_id == process.id,
                ProcessTransition.action_id == approve.id,
                ProcessTransition.from_status_id == in_approval.id,
                ProcessTransition.to_status_id == approved.id,
                ProcessTransition.role_id == approver_role.id,
                ProcessTransition.is_active.is_(True),
            )
        )
        assert transition is not None
        assert transition.effect == ProcessTransitionEffect.APPROVE_ADVANCE

        approver1 = session.scalar(
            select(User).where(User.login == dataset.approver_login)
        )
        assert approver1 is not None
        approver2 = _ensure_approver2(session)

        route = session.scalar(
            select(ApprovalRoute)
            .options(
                selectinload(ApprovalRoute.stages).selectinload(ApprovalStage.assignments)
            )
            .where(ApprovalRoute.request_type_id == dataset.vacation_type_id)
        )
        assert route is not None
        stages = sorted(route.stages, key=lambda item: item.sequence_no)
        assert stages, "vacation route must have stage 1 from seed"

        stage1 = stages[0]
        assert stage1.sequence_no == 1
        assert stage1.assignments
        stage1.assignments[0].assignment_kind = AssignmentKind.USER
        stage1.assignments[0].user_id = approver1.id
        stage1.assignments[0].role_id = None

        stage2 = next((s for s in stages if s.sequence_no == 2), None)
        if stage2 is None:
            stage2 = ApprovalStage(
                route_id=route.id,
                name="Согласование этап 2",
                sequence_no=2,
            )
            session.add(stage2)
            session.flush()
            session.add(
                StageAssignment(
                    stage_id=stage2.id,
                    assignment_kind=AssignmentKind.USER,
                    role_id=None,
                    user_id=approver2.id,
                )
            )
        else:
            if stage2.assignments:
                stage2.assignments[0].assignment_kind = AssignmentKind.USER
                stage2.assignments[0].user_id = approver2.id
                stage2.assignments[0].role_id = None
            else:
                session.add(
                    StageAssignment(
                        stage_id=stage2.id,
                        assignment_kind=AssignmentKind.USER,
                        role_id=None,
                        user_id=approver2.id,
                    )
                )

        # Ensure vacation field defs exist (seed already provides them).
        fields = session.scalars(
            select(RequestFieldDefinition).where(
                RequestFieldDefinition.request_type_id == dataset.vacation_type_id
            )
        ).all()
        assert any(f.code == "date_from" and f.data_type == FieldDataType.DATE for f in fields)

        session.commit()
        return MultiStageSetup(
            type_id=dataset.vacation_type_id,
            stage1_id=stage1.id,
            stage2_id=stage2.id,
            approver1_login=dataset.approver_login,
            approver2_login=APPROVER2_LOGIN,
            approve_action_id=dataset.approve_action_id,
            submit_action_id=dataset.submit_action_id,
            transition_effect=transition.effect,
        )
    finally:
        session.close()


def test_ac_app_05_multi_stage_approve_advance(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    """AC-APP-05 + AC-APP-05b: stage advance then final approve via Action Engine."""
    setup = _configure_two_stage_vacation_route(dataset)
    assert setup.transition_effect == ProcessTransitionEffect.APPROVE_ADVANCE

    emp = auth_header(client, dataset.employee_login)
    apr1 = auth_header(client, setup.approver1_login)
    apr2 = auth_header(client, setup.approver2_login)

    create = client.post(
        "/requests",
        headers=emp,
        json={"request_type_id": setup.type_id},
    )
    assert create.status_code == 201, create.text
    request_id = create.json()["id"]
    fill_valid_vacation_fields(request_id)

    # --- submit ---
    submit = _execute(client, emp, request_id, setup.submit_action_id)
    assert submit.status_code == 200, submit.text
    body = submit.json()
    assert body["status"]["code"] == "in_approval"
    assert body["current_stage_id"] == setup.stage1_id

    tasks_after_submit = _tasks(request_id)
    open_s1 = [
        t
        for t in tasks_after_submit
        if t.stage_id == setup.stage1_id and t.status == ApprovalTaskStatus.OPEN
    ]
    assert len(open_s1) == 1
    assert open_s1[0].assignee_user_id == _user_id(setup.approver1_login)

    notes_after_submit = _notifications(request_id)
    assert any(
        n.event_type == NotificationEventType.REQUEST_SUBMITTED
        and n.recipient_id == _user_id(setup.approver1_login)
        for n in notes_after_submit
    )

    # --- approve stage 1 → advance to stage 2 (approve_advance) ---
    advance = _execute(client, apr1, request_id, setup.approve_action_id)
    assert advance.status_code == 200, advance.text
    body = advance.json()
    assert body["status"]["code"] == "in_approval"
    assert body["current_stage_id"] == setup.stage2_id

    tasks_after_s1 = _tasks(request_id)
    s1_completed = [
        t
        for t in tasks_after_s1
        if t.stage_id == setup.stage1_id and t.status == ApprovalTaskStatus.COMPLETED
    ]
    assert len(s1_completed) == 1
    open_s2 = [
        t
        for t in tasks_after_s1
        if t.stage_id == setup.stage2_id and t.status == ApprovalTaskStatus.OPEN
    ]
    assert len(open_s2) == 1
    assert open_s2[0].assignee_user_id == _user_id(setup.approver2_login)

    history_after_s1 = _history(request_id)
    approve_events = [e for e in history_after_s1 if e.action == "approve"]
    assert len(approve_events) == 1
    assert approve_events[0].actor_id == _user_id(setup.approver1_login)
    assert approve_events[0].from_state == "in_approval"
    assert approve_events[0].to_state == "in_approval"

    notes_after_s1 = _notifications(request_id)
    advance_notes = [
        n
        for n in notes_after_s1
        if n.event_type == NotificationEventType.REQUEST_APPROVED
        and n.recipient_id == _user_id(setup.approver2_login)
    ]
    assert len(advance_notes) == 1
    assert advance_notes[0].approval_task_id == open_s2[0].id

    # --- approve stage 2 → final approved ---
    final = _execute(client, apr2, request_id, setup.approve_action_id)
    assert final.status_code == 200, final.text
    body = final.json()
    assert body["status"]["code"] == "approved"
    assert body["current_stage_id"] is None

    tasks_final = _tasks(request_id)
    s2_completed = [
        t
        for t in tasks_final
        if t.stage_id == setup.stage2_id and t.status == ApprovalTaskStatus.COMPLETED
    ]
    assert len(s2_completed) == 1
    assert not any(t.status == ApprovalTaskStatus.OPEN for t in tasks_final)

    history_final = _history(request_id)
    approve_events = [e for e in history_final if e.action == "approve"]
    assert len(approve_events) == 2
    final_event = approve_events[-1]
    assert final_event.actor_id == _user_id(setup.approver2_login)
    assert final_event.from_state == "in_approval"
    assert final_event.to_state == "approved"

    notes_final = _notifications(request_id)
    initiator_notes = [
        n
        for n in notes_final
        if n.event_type == NotificationEventType.REQUEST_APPROVED
        and n.recipient_id == _user_id(dataset.employee_login)
    ]
    assert len(initiator_notes) >= 1
    assert initiator_notes[-1].approval_task_id == s2_completed[0].id

    # Sanity: still one active approve_advance ProcessTransition (engine path, not test logic).
    session = get_session_factory()()
    try:
        process = session.scalar(select(Process).where(Process.code == "employee_requests"))
        assert process is not None
        rt = session.get(RequestType, setup.type_id)
        assert rt is not None and rt.process_id == process.id
        tr = session.scalar(
            select(ProcessTransition).where(
                ProcessTransition.process_id == process.id,
                ProcessTransition.action_id == setup.approve_action_id,
                ProcessTransition.effect == ProcessTransitionEffect.APPROVE_ADVANCE,
                ProcessTransition.is_active.is_(True),
            )
        )
        assert tr is not None
    finally:
        session.close()
