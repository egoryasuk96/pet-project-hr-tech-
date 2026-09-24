"""E3.2 Target Action Engine API tests."""

from __future__ import annotations

import threading
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.errors import AppError
from app.db.session import get_session_factory
from app.domain.approval import ApprovalTask
from app.domain.enums import ApprovalTaskStatus
from app.domain.identity import User
from app.domain.request import Request
from app.domain.routing import ApprovalRoute, ApprovalStage, StageAssignment
from app.services import action_engine
from tests.conftest import ApiDataset, auth_header


def _error_code(response) -> str:
    return response.json()["error"]["code"]


def _create_draft(client: TestClient, headers: dict[str, str], type_id: int) -> int:
    response = client.post("/requests", headers=headers, json={"request_type_id": type_id})
    assert response.status_code == 201, response.text
    request_id = response.json()["id"]
    from tests.conftest import fill_valid_vacation_fields

    fill_valid_vacation_fields(request_id)
    return request_id


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


def _open_tasks(request_id: int) -> list[ApprovalTask]:
    session = get_session_factory()()
    try:
        return list(
            session.scalars(
                select(ApprovalTask).where(
                    ApprovalTask.request_id == request_id,
                    ApprovalTask.status == ApprovalTaskStatus.OPEN,
                )
            ).all()
        )
    finally:
        session.close()


def _assignee_from_stage_assignment(type_id: int) -> UUID:
    session = get_session_factory()()
    try:
        route = session.scalar(
            select(ApprovalRoute)
            .options(
                selectinload(ApprovalRoute.stages).selectinload(ApprovalStage.assignments)
            )
            .where(ApprovalRoute.request_type_id == type_id)
        )
        assert route and route.stages
        stage = sorted(route.stages, key=lambda item: item.sequence_no)[0]
        assert stage.assignments
        assignment: StageAssignment = stage.assignments[0]
        assert assignment.user_id is not None
        return assignment.user_id
    finally:
        session.close()


def _user_id(login: str) -> UUID:
    session = get_session_factory()()
    try:
        user = session.scalar(select(User).where(User.login == login))
        assert user is not None
        return user.id
    finally:
        session.close()


def test_submit_draft_creates_task_and_stage(
    client: TestClient,
    dataset: ApiDataset,
) -> None:
    headers = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, headers, dataset.vacation_type_id)
    expected_assignee = _assignee_from_stage_assignment(dataset.vacation_type_id)

    response = _execute(client, headers, request_id, dataset.submit_action_id)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"]["code"] == "in_approval"
    assert body["current_stage_id"] is not None

    tasks = _open_tasks(request_id)
    assert len(tasks) == 1
    assert tasks[0].assignee_user_id == expected_assignee
    assert expected_assignee == _user_id(dataset.approver_login)


def test_cancel_draft_no_task(client: TestClient, dataset: ApiDataset) -> None:
    headers = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, headers, dataset.vacation_type_id)

    response = _execute(client, headers, request_id, dataset.cancel_action_id)
    assert response.status_code == 200, response.text
    assert response.json()["status"]["code"] == "cancelled"
    assert response.json()["current_stage_id"] is None
    assert _open_tasks(request_id) == []


def test_approve_completes_request(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    assert _execute(client, emp, request_id, dataset.submit_action_id).status_code == 200

    apr = auth_header(client, dataset.approver_login)
    response = _execute(client, apr, request_id, dataset.approve_action_id)
    assert response.status_code == 200, response.text
    assert response.json()["status"]["code"] == "approved"
    assert response.json()["current_stage_id"] is None

    session = get_session_factory()()
    try:
        tasks = session.scalars(
            select(ApprovalTask).where(ApprovalTask.request_id == request_id)
        ).all()
        assert tasks
        assert all(task.status != ApprovalTaskStatus.OPEN for task in tasks)
        assert any(task.status == ApprovalTaskStatus.COMPLETED for task in tasks)
    finally:
        session.close()


def _seed_self_approval_request(dataset: ApiDataset) -> int:
    """Initiator == assignee (approver.demo) with one open task on stage 1."""
    session = get_session_factory()()
    try:
        approver = session.scalar(
            select(User)
            .options(selectinload(User.role))
            .where(User.login == dataset.approver_login)
        )
        assert approver is not None
        route = session.scalar(
            select(ApprovalRoute)
            .options(selectinload(ApprovalRoute.stages))
            .where(ApprovalRoute.request_type_id == dataset.vacation_type_id)
        )
        assert route and route.stages
        stage = sorted(route.stages, key=lambda item: item.sequence_no)[0]
        request = Request(
            request_type_id=dataset.vacation_type_id,
            initiator_user_id=approver.id,
            status_id=dataset.in_approval_status_id,
            current_stage_id=stage.id,
        )
        session.add(request)
        session.flush()
        session.add(
            ApprovalTask(
                request_id=request.id,
                stage_id=stage.id,
                assignee_user_id=approver.id,
                status=ApprovalTaskStatus.OPEN,
            )
        )
        session.commit()
        return request.id
    finally:
        session.close()


def _add_sibling_open_task(request_id: int, assignee_user_id: UUID) -> int:
    """Insert a second open ApprovalTask on the request's current stage."""
    session = get_session_factory()()
    try:
        request = session.get(Request, request_id)
        assert request is not None
        assert request.current_stage_id is not None
        sibling = ApprovalTask(
            request_id=request.id,
            stage_id=request.current_stage_id,
            assignee_user_id=assignee_user_id,
            status=ApprovalTaskStatus.OPEN,
        )
        session.add(sibling)
        session.commit()
        return sibling.id
    finally:
        session.close()


def _stage_id_after_submit(client: TestClient, headers: dict[str, str], request_id: int) -> int:
    card = client.get(f"/requests/{request_id}", headers=headers)
    assert card.status_code == 200, card.text
    stage_id = card.json()["current_stage_id"]
    assert stage_id is not None
    return stage_id


def test_self_approval_forbidden(client: TestClient, dataset: ApiDataset) -> None:
    """Initiator is approver: approve must fail BR-21."""
    request_id = _seed_self_approval_request(dataset)
    apr = auth_header(client, dataset.approver_login)
    response = _execute(client, apr, request_id, dataset.approve_action_id)
    assert response.status_code == 403
    assert _error_code(response) == "FORBIDDEN_APPROVAL"


def test_self_reject_forbidden(client: TestClient, dataset: ApiDataset) -> None:
    """Initiator is approver: reject must fail BR-21."""
    request_id = _seed_self_approval_request(dataset)
    apr = auth_header(client, dataset.approver_login)
    response = _execute(
        client, apr, request_id, dataset.reject_action_id, comment="Нельзя"
    )
    assert response.status_code == 403
    assert _error_code(response) == "FORBIDDEN_APPROVAL"


def test_self_return_forbidden(client: TestClient, dataset: ApiDataset) -> None:
    """Initiator is approver: return must fail BR-21."""
    request_id = _seed_self_approval_request(dataset)
    apr = auth_header(client, dataset.approver_login)
    response = _execute(
        client, apr, request_id, dataset.return_action_id, comment="Нельзя"
    )
    assert response.status_code == 403
    assert _error_code(response) == "FORBIDDEN_APPROVAL"


def test_reject_requires_comment(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    assert _execute(client, emp, request_id, dataset.submit_action_id).status_code == 200

    apr = auth_header(client, dataset.approver_login)
    response = _execute(client, apr, request_id, dataset.reject_action_id, comment="   ")
    assert response.status_code == 422
    assert _error_code(response) == "VALIDATION"


def test_reject_with_comment(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    assert _execute(client, emp, request_id, dataset.submit_action_id).status_code == 200
    stage_id = _stage_id_after_submit(client, emp, request_id)

    apr = auth_header(client, dataset.approver_login)
    response = _execute(
        client, apr, request_id, dataset.reject_action_id, comment="Не согласовано"
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"]["code"] == "rejected"
    assert response.json()["current_stage_id"] == stage_id

    session = get_session_factory()()
    try:
        task = session.scalar(
            select(ApprovalTask).where(ApprovalTask.request_id == request_id)
        )
        assert task is not None
        assert task.status == ApprovalTaskStatus.COMPLETED
        assert task.comment == "Не согласовано"
        assert task.completed_at is not None
    finally:
        session.close()


def test_reject_cancels_sibling_open_tasks(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    assert _execute(client, emp, request_id, dataset.submit_action_id).status_code == 200
    stage_id = _stage_id_after_submit(client, emp, request_id)
    sibling_id = _add_sibling_open_task(request_id, _user_id(dataset.admin_login))

    apr = auth_header(client, dataset.approver_login)
    response = _execute(
        client, apr, request_id, dataset.reject_action_id, comment="Отклонено"
    )
    assert response.status_code == 200, response.text
    assert response.json()["current_stage_id"] == stage_id
    assert _open_tasks(request_id) == []

    session = get_session_factory()()
    try:
        tasks = {
            task.id: task
            for task in session.scalars(
                select(ApprovalTask).where(ApprovalTask.request_id == request_id)
            ).all()
        }
        assert len(tasks) == 2
        actor = next(
            task
            for task in tasks.values()
            if task.assignee_user_id == _user_id(dataset.approver_login)
        )
        sibling = tasks[sibling_id]
        assert actor.status == ApprovalTaskStatus.COMPLETED
        assert sibling.status == ApprovalTaskStatus.CANCELLED
        assert sibling.completed_at is not None
    finally:
        session.close()


def test_return_requires_comment(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    assert _execute(client, emp, request_id, dataset.submit_action_id).status_code == 200

    apr = auth_header(client, dataset.approver_login)
    response = _execute(client, apr, request_id, dataset.return_action_id)
    assert response.status_code == 422
    assert _error_code(response) == "VALIDATION"


def test_return_with_comment(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    assert _execute(client, emp, request_id, dataset.submit_action_id).status_code == 200
    stage_id = _stage_id_after_submit(client, emp, request_id)

    apr = auth_header(client, dataset.approver_login)
    response = _execute(
        client, apr, request_id, dataset.return_action_id, comment="Уточните даты"
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"]["code"] == "returned"
    assert response.json()["current_stage_id"] == stage_id
    assert _open_tasks(request_id) == []

    session = get_session_factory()()
    try:
        task = session.scalar(
            select(ApprovalTask).where(ApprovalTask.request_id == request_id)
        )
        assert task is not None
        assert task.status == ApprovalTaskStatus.COMPLETED
        assert task.comment == "Уточните даты"
    finally:
        session.close()


def test_return_cancels_sibling_open_tasks(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    assert _execute(client, emp, request_id, dataset.submit_action_id).status_code == 200
    stage_id = _stage_id_after_submit(client, emp, request_id)
    sibling_id = _add_sibling_open_task(request_id, _user_id(dataset.admin_login))

    apr = auth_header(client, dataset.approver_login)
    response = _execute(
        client, apr, request_id, dataset.return_action_id, comment="На доработку"
    )
    assert response.status_code == 200, response.text
    assert response.json()["current_stage_id"] == stage_id
    assert _open_tasks(request_id) == []

    session = get_session_factory()()
    try:
        tasks = {
            task.id: task
            for task in session.scalars(
                select(ApprovalTask).where(ApprovalTask.request_id == request_id)
            ).all()
        }
        assert len(tasks) == 2
        actor = next(
            task
            for task in tasks.values()
            if task.assignee_user_id == _user_id(dataset.approver_login)
        )
        sibling = tasks[sibling_id]
        assert actor.status == ApprovalTaskStatus.COMPLETED
        assert sibling.status == ApprovalTaskStatus.CANCELLED
        assert sibling.completed_at is not None
    finally:
        session.close()


def test_returned_submit_creates_new_task(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    assert _execute(client, emp, request_id, dataset.submit_action_id).status_code == 200
    apr = auth_header(client, dataset.approver_login)
    assert (
        _execute(client, apr, request_id, dataset.return_action_id, comment="fix").status_code
        == 200
    )

    response = _execute(client, emp, request_id, dataset.submit_action_id)
    assert response.status_code == 200, response.text
    assert response.json()["status"]["code"] == "in_approval"
    assert response.json()["current_stage_id"] is not None
    assert len(_open_tasks(request_id)) == 1


def test_returned_cancel(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    assert _execute(client, emp, request_id, dataset.submit_action_id).status_code == 200
    apr = auth_header(client, dataset.approver_login)
    assert (
        _execute(client, apr, request_id, dataset.return_action_id, comment="fix").status_code
        == 200
    )

    response = _execute(client, emp, request_id, dataset.cancel_action_id)
    assert response.status_code == 200, response.text
    assert response.json()["status"]["code"] == "cancelled"


def test_employee_cannot_approve(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    assert _execute(client, emp, request_id, dataset.submit_action_id).status_code == 200

    response = _execute(client, emp, request_id, dataset.approve_action_id)
    assert response.status_code == 409
    assert _error_code(response) == "REQUEST_ACTION_NOT_ALLOWED"


def test_approver_cannot_submit(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)

    apr = auth_header(client, dataset.approver_login)
    response = _execute(client, apr, request_id, dataset.submit_action_id)
    assert response.status_code == 409
    assert _error_code(response) == "REQUEST_ACTION_NOT_ALLOWED"


def test_admin_no_approve_without_transition(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    assert _execute(client, emp, request_id, dataset.submit_action_id).status_code == 200

    adm = auth_header(client, dataset.admin_login)
    response = _execute(client, adm, request_id, dataset.approve_action_id)
    assert response.status_code == 409
    assert _error_code(response) == "REQUEST_ACTION_NOT_ALLOWED"


def test_unknown_action_id(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    response = _execute(client, emp, request_id, action_id=999999)
    assert response.status_code == 404
    assert _error_code(response) == "NOT_FOUND"


def test_action_not_allowed_for_state(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    # approve is not allowed from draft for employee (or anyone without matching transition)
    response = _execute(client, emp, request_id, dataset.approve_action_id)
    assert response.status_code == 409
    assert _error_code(response) == "REQUEST_ACTION_NOT_ALLOWED"


def test_request_not_found(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    response = _execute(client, emp, 99999, dataset.submit_action_id)
    assert response.status_code == 404
    assert _error_code(response) == "NOT_FOUND"


def test_concurrent_approve_only_one_succeeds(client: TestClient, dataset: ApiDataset) -> None:
    emp = auth_header(client, dataset.employee_login)
    request_id = _create_draft(client, emp, dataset.vacation_type_id)
    assert _execute(client, emp, request_id, dataset.submit_action_id).status_code == 200

    barrier = threading.Barrier(2)
    outcomes: list[str] = []
    lock = threading.Lock()

    def worker() -> None:
        session = get_session_factory()()
        try:
            user = session.scalar(
                select(User)
                .options(selectinload(User.role))
                .where(User.login == dataset.approver_login)
            )
            assert user is not None
            barrier.wait(timeout=10)
            try:
                action_engine.execute_action(
                    session,
                    user,
                    request_id,
                    dataset.approve_action_id,
                    comment=None,
                )
                with lock:
                    outcomes.append("ok")
            except AppError as exc:
                session.rollback()
                with lock:
                    outcomes.append(exc.error_code)
        finally:
            session.close()

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    assert outcomes.count("ok") == 1, outcomes
    assert outcomes.count("TASK_DONE") == 1, outcomes

    session = get_session_factory()()
    try:
        request = session.get(Request, request_id)
        assert request is not None
        from app.domain.process import Status

        st = session.get(Status, request.status_id)
        assert st is not None
        assert st.code == "approved"
        open_tasks = session.scalars(
            select(ApprovalTask).where(
                ApprovalTask.request_id == request_id,
                ApprovalTask.status == ApprovalTaskStatus.OPEN,
            )
        ).all()
        assert open_tasks == []
    finally:
        session.close()
