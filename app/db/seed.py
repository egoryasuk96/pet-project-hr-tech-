"""Idempotent Target E2 demo seed for local development (NFR-DEP-02).

Ensures org, RBAC, process/status/action/transition matrix, catalog and live
routing for the MVP vertical slice. Does not insert runtime requests/tasks.

Usage:
    python -m app.db.seed
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import get_session_factory
from app.domain import (
    Action,
    ApprovalRoute,
    ApprovalStage,
    AssignmentKind,
    Company,
    Department,
    Dictionary,
    DictionaryItem,
    Employee,
    FieldDataType,
    Process,
    ProcessTransition,
    ProcessTransitionEffect,
    RequestFieldDefinition,
    RequestType,
    Role,
    RoleCode,
    StageAssignment,
    Status,
    User,
)

PROCESS_CODE = "employee_requests"
PROCESS_NAME = "Employee requests"

ROLE_SPECS: tuple[tuple[RoleCode, str], ...] = (
    (RoleCode.EMPLOYEE, "Employee"),
    (RoleCode.APPROVER, "Approver"),
    (RoleCode.ADMIN, "Administrator"),
)

STATUS_SPECS: tuple[tuple[str, str], ...] = (
    ("draft", "Draft"),
    ("in_approval", "In approval"),
    ("returned", "Returned"),
    ("approved", "Approved"),
    ("rejected", "Rejected"),
    ("cancelled", "Cancelled"),
)

ACTION_SPECS: tuple[tuple[str, str], ...] = (
    ("submit", "Submit"),
    ("cancel", "Cancel"),
    ("approve", "Approve"),
    ("reject", "Reject"),
    ("return", "Return"),
)

# (sort_order, action_code, from_status, to_status, effect, role_code)
TRANSITION_SPECS: tuple[
    tuple[int, str, str, str, ProcessTransitionEffect, RoleCode],
    ...,
] = (
    (10, "submit", "draft", "in_approval", ProcessTransitionEffect.STATUS_ONLY, RoleCode.EMPLOYEE),
    (20, "submit", "returned", "in_approval", ProcessTransitionEffect.STATUS_ONLY, RoleCode.EMPLOYEE),
    (30, "cancel", "draft", "cancelled", ProcessTransitionEffect.STATUS_ONLY, RoleCode.EMPLOYEE),
    (40, "cancel", "returned", "cancelled", ProcessTransitionEffect.STATUS_ONLY, RoleCode.EMPLOYEE),
    (50, "approve", "in_approval", "approved", ProcessTransitionEffect.APPROVE_ADVANCE, RoleCode.APPROVER),
    (60, "reject", "in_approval", "rejected", ProcessTransitionEffect.STATUS_ONLY, RoleCode.APPROVER),
    (70, "return", "in_approval", "returned", ProcessTransitionEffect.STATUS_ONLY, RoleCode.APPROVER),
)

COMPANY_NAME = "Demo Company"
STAGE_NAME = "Согласование руководителем"
CERTIFICATE_DICTIONARY_NAME = "Виды справок"


@dataclass(frozen=True)
class DemoPerson:
    login: str
    role: RoleCode
    employee_number: str
    first_name: str
    last_name: str
    department_name: str
    position: str


DEMO_PEOPLE = (
    DemoPerson(
        login="employee.demo",
        role=RoleCode.EMPLOYEE,
        employee_number="EMP-employee.demo",
        first_name="Иван",
        last_name="Сотрудников",
        department_name="IT",
        position="Аналитик",
    ),
    DemoPerson(
        login="approver.demo",
        role=RoleCode.APPROVER,
        employee_number="EMP-approver.demo",
        first_name="Мария",
        last_name="Руководителева",
        department_name="IT",
        position="Руководитель",
    ),
    DemoPerson(
        login="admin.demo",
        role=RoleCode.ADMIN,
        employee_number="EMP-admin.demo",
        first_name="Пётр",
        last_name="Админов",
        department_name="HR",
        position="HR-администратор",
    ),
)


def _demo_password_hash() -> str | None:
    password = get_settings().demo_password
    if password is None or password == "":
        return None
    return hash_password(password)


def _ensure_role(session: Session, code: RoleCode, name: str) -> Role:
    role = session.scalar(select(Role).where(Role.code == code))
    if role is None:
        role = Role(code=code, name=name)
        session.add(role)
        session.flush()
    else:
        role.name = name
    return role


def _ensure_company(session: Session) -> Company:
    company = session.scalar(select(Company).where(Company.name == COMPANY_NAME))
    if company is None:
        company = Company(name=COMPANY_NAME, active=True)
        session.add(company)
        session.flush()
    else:
        company.active = True
    return company


def _ensure_department(session: Session, company: Company, name: str) -> Department:
    department = session.scalar(
        select(Department).where(
            Department.company_id == company.id,
            Department.name == name,
        )
    )
    if department is None:
        department = Department(company_id=company.id, name=name, active=True)
        session.add(department)
        session.flush()
    else:
        department.active = True
    return department


def _ensure_employee(
    session: Session,
    *,
    department: Department,
    person: DemoPerson,
) -> Employee:
    employee = session.scalar(
        select(Employee).where(Employee.employee_number == person.employee_number)
    )
    if employee is None:
        employee = Employee(
            employee_number=person.employee_number,
            first_name=person.first_name,
            last_name=person.last_name,
            middle_name=None,
            department_id=department.id,
            manager_employee_id=None,
            position=person.position,
            active=True,
        )
        session.add(employee)
        session.flush()
    else:
        employee.first_name = person.first_name
        employee.last_name = person.last_name
        employee.department_id = department.id
        employee.position = person.position
        employee.active = True
    return employee


def _ensure_user(
    session: Session,
    *,
    person: DemoPerson,
    role: Role,
    employee: Employee,
    password_hash: str | None,
) -> User:
    user = session.scalar(select(User).where(User.login == person.login))
    if user is None:
        user = User(
            login=person.login,
            password_hash=password_hash,
            is_active=True,
            role_id=role.id,
            employee_id=employee.id,
        )
        session.add(user)
        session.flush()
    else:
        user.role_id = role.id
        user.employee_id = employee.id
        user.is_active = True
        if password_hash is not None:
            user.password_hash = password_hash
    return user


def _ensure_process(session: Session) -> Process:
    process = session.scalar(select(Process).where(Process.code == PROCESS_CODE))
    if process is None:
        process = Process(
            code=PROCESS_CODE,
            name=PROCESS_NAME,
            description="Default process for employee service request types",
            active=True,
        )
        session.add(process)
        session.flush()
    else:
        process.name = PROCESS_NAME
        process.active = True
    return process


def _ensure_status(session: Session, code: str, name: str) -> Status:
    status = session.scalar(select(Status).where(Status.code == code))
    if status is None:
        status = Status(code=code, name=name, description=None, active=True)
        session.add(status)
        session.flush()
    else:
        status.name = name
        status.active = True
    return status


def _ensure_action(session: Session, code: str, name: str) -> Action:
    action = session.scalar(select(Action).where(Action.code == code))
    if action is None:
        action = Action(code=code, name=name, description=None, active=True)
        session.add(action)
        session.flush()
    else:
        action.name = name
        action.active = True
    return action


def _ensure_transition(
    session: Session,
    *,
    process: Process,
    action: Action,
    from_status: Status,
    to_status: Status,
    role: Role,
    effect: ProcessTransitionEffect,
    sort_order: int,
) -> ProcessTransition:
    transition = session.scalar(
        select(ProcessTransition).where(
            ProcessTransition.process_id == process.id,
            ProcessTransition.action_id == action.id,
            ProcessTransition.from_status_id == from_status.id,
            ProcessTransition.to_status_id == to_status.id,
            ProcessTransition.role_id == role.id,
        )
    )
    if transition is None:
        transition = ProcessTransition(
            process_id=process.id,
            action_id=action.id,
            from_status_id=from_status.id,
            to_status_id=to_status.id,
            role_id=role.id,
            effect=effect,
            is_active=True,
            sort_order=sort_order,
        )
        session.add(transition)
        session.flush()
    else:
        transition.effect = effect
        transition.is_active = True
        transition.sort_order = sort_order
    return transition


def _ensure_dictionary(session: Session, name: str) -> Dictionary:
    dictionary = session.scalar(select(Dictionary).where(Dictionary.name == name))
    if dictionary is None:
        dictionary = Dictionary(name=name)
        session.add(dictionary)
        session.flush()
    return dictionary


def _ensure_dictionary_item(
    session: Session,
    dictionary: Dictionary,
    code: str,
    name: str,
) -> DictionaryItem:
    item = session.scalar(
        select(DictionaryItem).where(
            DictionaryItem.dictionary_id == dictionary.id,
            DictionaryItem.code == code,
        )
    )
    if item is None:
        item = DictionaryItem(
            dictionary_id=dictionary.id,
            code=code,
            name=name,
            active=True,
        )
        session.add(item)
        session.flush()
    else:
        item.name = name
        item.active = True
    return item


def _ensure_request_type(
    session: Session,
    *,
    process: Process,
    code: str,
    name: str,
    description: str,
) -> RequestType:
    request_type = session.scalar(select(RequestType).where(RequestType.code == code))
    if request_type is None:
        request_type = RequestType(
            process_id=process.id,
            code=code,
            name=name,
            description=description,
            active=True,
        )
        session.add(request_type)
        session.flush()
    else:
        request_type.process_id = process.id
        request_type.name = name
        request_type.description = description
        request_type.active = True
    return request_type


def _ensure_field(
    session: Session,
    request_type: RequestType,
    *,
    code: str,
    name: str,
    data_type: FieldDataType,
    required: bool,
    order_no: int,
    dictionary: Dictionary | None = None,
) -> RequestFieldDefinition:
    field = session.scalar(
        select(RequestFieldDefinition).where(
            RequestFieldDefinition.request_type_id == request_type.id,
            RequestFieldDefinition.code == code,
        )
    )
    if field is None:
        field = RequestFieldDefinition(
            request_type_id=request_type.id,
            code=code,
            name=name,
            data_type=data_type,
            required=required,
            order_no=order_no,
            dictionary_id=dictionary.id if dictionary is not None else None,
        )
        session.add(field)
        session.flush()
    else:
        field.name = name
        field.data_type = data_type
        field.required = required
        field.order_no = order_no
        field.dictionary_id = dictionary.id if dictionary is not None else None
    return field


def _ensure_route_with_approver(
    session: Session,
    request_type: RequestType,
    approver: User,
) -> None:
    route = session.scalar(
        select(ApprovalRoute).where(ApprovalRoute.request_type_id == request_type.id)
    )
    if route is None:
        route = ApprovalRoute(request_type_id=request_type.id)
        session.add(route)
        session.flush()

    stage = session.scalar(
        select(ApprovalStage).where(
            ApprovalStage.route_id == route.id,
            ApprovalStage.sequence_no == 1,
        )
    )
    if stage is None:
        stage = ApprovalStage(route_id=route.id, name=STAGE_NAME, sequence_no=1)
        session.add(stage)
        session.flush()
    else:
        stage.name = STAGE_NAME

    assignment = session.scalar(
        select(StageAssignment).where(StageAssignment.stage_id == stage.id)
    )
    if assignment is None:
        assignment = StageAssignment(
            stage_id=stage.id,
            assignment_kind=AssignmentKind.USER,
            role_id=None,
            user_id=approver.id,
        )
        session.add(assignment)
        session.flush()
    else:
        assignment.assignment_kind = AssignmentKind.USER
        assignment.role_id = None
        assignment.user_id = approver.id


def seed(session: Session) -> None:
    """Upsert Target E2 demo configuration. Safe to run repeatedly."""
    roles = {
        code: _ensure_role(session, code, name) for code, name in ROLE_SPECS
    }

    company = _ensure_company(session)
    departments = {
        name: _ensure_department(session, company, name) for name in ("IT", "HR")
    }

    password_hash = _demo_password_hash()
    users_by_login: dict[str, User] = {}
    for person in DEMO_PEOPLE:
        employee = _ensure_employee(
            session,
            department=departments[person.department_name],
            person=person,
        )
        user = _ensure_user(
            session,
            person=person,
            role=roles[person.role],
            employee=employee,
            password_hash=password_hash,
        )
        users_by_login[person.login] = user

    process = _ensure_process(session)
    statuses = {
        code: _ensure_status(session, code, name) for code, name in STATUS_SPECS
    }
    actions = {
        code: _ensure_action(session, code, name) for code, name in ACTION_SPECS
    }

    for sort_order, action_code, from_code, to_code, effect, role_code in TRANSITION_SPECS:
        _ensure_transition(
            session,
            process=process,
            action=actions[action_code],
            from_status=statuses[from_code],
            to_status=statuses[to_code],
            role=roles[role_code],
            effect=effect,
            sort_order=sort_order,
        )

    dictionary = _ensure_dictionary(session, CERTIFICATE_DICTIONARY_NAME)
    _ensure_dictionary_item(session, dictionary, "employment", "Справка с места работы")
    _ensure_dictionary_item(session, dictionary, "income", "Справка о доходах")

    vacation = _ensure_request_type(
        session,
        process=process,
        code="vacation",
        name="Отпуск",
        description="Заявка на ежегодный оплачиваемый отпуск",
    )
    _ensure_field(
        session,
        vacation,
        code="date_from",
        name="Дата начала",
        data_type=FieldDataType.DATE,
        required=True,
        order_no=1,
    )
    _ensure_field(
        session,
        vacation,
        code="date_to",
        name="Дата окончания",
        data_type=FieldDataType.DATE,
        required=True,
        order_no=2,
    )
    _ensure_field(
        session,
        vacation,
        code="comment",
        name="Комментарий",
        data_type=FieldDataType.TEXT,
        required=False,
        order_no=3,
    )

    certificate = _ensure_request_type(
        session,
        process=process,
        code="certificate",
        name="Справка",
        description="Заявка на кадровую справку",
    )
    _ensure_field(
        session,
        certificate,
        code="certificate_kind",
        name="Вид справки",
        data_type=FieldDataType.CATALOG,
        required=True,
        order_no=1,
        dictionary=dictionary,
    )
    _ensure_field(
        session,
        certificate,
        code="note",
        name="Примечание",
        data_type=FieldDataType.TEXT,
        required=False,
        order_no=2,
    )

    approver = users_by_login["approver.demo"]
    _ensure_route_with_approver(session, vacation, approver)
    _ensure_route_with_approver(session, certificate, approver)


def _print_summary(session: Session) -> None:
    counts = {
        "roles": len(session.scalars(select(Role)).all()),
        "users": len(session.scalars(select(User)).all()),
        "employees": len(session.scalars(select(Employee)).all()),
        "processes": len(session.scalars(select(Process)).all()),
        "statuses": len(session.scalars(select(Status)).all()),
        "actions": len(session.scalars(select(Action)).all()),
        "transitions": len(session.scalars(select(ProcessTransition)).all()),
        "request_types": len(session.scalars(select(RequestType)).all()),
    }
    print(
        "Seed complete: "
        f"{counts['roles']} roles, {counts['users']} users, "
        f"{counts['employees']} employees, {counts['processes']} processes, "
        f"{counts['statuses']} statuses, {counts['actions']} actions, "
        f"{counts['transitions']} transitions, {counts['request_types']} request types."
    )


def main() -> None:
    session_factory = get_session_factory()
    session = session_factory()
    try:
        seed(session)
        session.commit()
        _print_summary(session)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
