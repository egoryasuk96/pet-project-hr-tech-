"""Idempotent demo seed for local development (NFR-DEP-02).

Creates roles, demo users, two active request types with fields and a valid
approval route. Does not insert requests, tasks, comments, history, or notifications.

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
    ApprovalRoute,
    ApprovalStage,
    AssignmentKind,
    Dictionary,
    DictionaryItem,
    FieldDataType,
    RequestFieldDefinition,
    RequestType,
    Role,
    RoleCode,
    StageAssignment,
    User,
    UserRole,
)


@dataclass(frozen=True)
class DemoUser:
    login: str
    full_name: str
    email: str
    position: str
    department: str
    role: RoleCode


DEMO_USERS = (
    DemoUser(
        login="employee.demo",
        full_name="Иван Сотрудников",
        email="employee.demo@example.local",
        position="Аналитик",
        department="IT",
        role=RoleCode.EMPLOYEE,
    ),
    DemoUser(
        login="approver.demo",
        full_name="Мария Руководителева",
        email="approver.demo@example.local",
        position="Руководитель",
        department="IT",
        role=RoleCode.APPROVER,
    ),
    DemoUser(
        login="admin.demo",
        full_name="Пётр Админов",
        email="admin.demo@example.local",
        position="HR-администратор",
        department="HR",
        role=RoleCode.ADMIN,
    ),
)

VACATION_TYPE_NAME = "Отпуск"
CERTIFICATE_TYPE_NAME = "Справка"
CERTIFICATE_DICTIONARY_NAME = "Виды справок"
STAGE_NAME = "Согласование руководителем"


def _get_or_create_role(session: Session, code: RoleCode) -> Role:
    role = session.scalar(select(Role).where(Role.code == code))
    if role is None:
        role = Role(code=code)
        session.add(role)
        session.flush()
    return role


def _demo_password_hash() -> str | None:
    """Hash DEMO_PASSWORD from the environment. None if the variable is unset."""
    password = get_settings().demo_password
    if password is None or password == "":
        return None
    return hash_password(password)


def _get_or_create_user(session: Session, spec: DemoUser, password_hash: str | None) -> User:
    user = session.scalar(select(User).where(User.login == spec.login))
    if user is None:
        user = User(login=spec.login, password_hash=password_hash)
        session.add(user)
    elif password_hash is not None:
        user.password_hash = password_hash
    user.full_name = spec.full_name
    user.email = spec.email
    user.position = spec.position
    user.department = spec.department
    user.is_active = True
    session.flush()
    return user


def _ensure_user_role(session: Session, user: User, role: Role) -> None:
    existing = session.scalar(
        select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == role.id)
    )
    if existing is None:
        session.add(UserRole(user_id=user.id, role_id=role.id))
        session.flush()


def _get_or_create_dictionary(session: Session, name: str) -> Dictionary:
    dictionary = session.scalar(select(Dictionary).where(Dictionary.name == name))
    if dictionary is None:
        dictionary = Dictionary(name=name)
        session.add(dictionary)
        session.flush()
    else:
        dictionary.name = name
    return dictionary


def _get_or_create_dictionary_item(
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
        item = DictionaryItem(dictionary_id=dictionary.id, code=code)
        session.add(item)
    item.name = name
    item.is_active = True
    session.flush()
    return item


def _get_or_create_request_type(
    session: Session,
    name: str,
    description: str,
) -> RequestType:
    request_type = session.scalar(select(RequestType).where(RequestType.name == name))
    if request_type is None:
        request_type = RequestType(name=name)
        session.add(request_type)
    request_type.description = description
    request_type.is_active = True
    session.flush()
    return request_type


def _get_or_create_field(
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
        field = RequestFieldDefinition(request_type_id=request_type.id, code=code)
        session.add(field)
    field.name = name
    field.data_type = data_type
    field.required = required
    field.order_no = order_no
    field.dictionary_id = dictionary.id if dictionary is not None else None
    session.flush()
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
        stage = ApprovalStage(route_id=route.id, sequence_no=1)
        session.add(stage)
    stage.name = STAGE_NAME
    session.flush()

    assignment = session.scalar(
        select(StageAssignment).where(StageAssignment.stage_id == stage.id)
    )
    if assignment is None:
        assignment = StageAssignment(stage_id=stage.id)
        session.add(assignment)
    assignment.assignment_kind = AssignmentKind.USER
    assignment.role_id = None
    assignment.user_id = approver.id
    session.flush()


def seed(session: Session) -> None:
    """Upsert the minimal demo dataset. Safe to run repeatedly."""
    roles = {code: _get_or_create_role(session, code) for code in RoleCode}

    password_hash = _demo_password_hash()
    users_by_login: dict[str, User] = {}
    for spec in DEMO_USERS:
        user = _get_or_create_user(session, spec, password_hash)
        _ensure_user_role(session, user, roles[spec.role])
        users_by_login[spec.login] = user

    approver = users_by_login["approver.demo"]

    dictionary = _get_or_create_dictionary(session, CERTIFICATE_DICTIONARY_NAME)
    _get_or_create_dictionary_item(session, dictionary, "employment", "Справка с места работы")
    _get_or_create_dictionary_item(session, dictionary, "income", "Справка о доходах")

    vacation = _get_or_create_request_type(
        session,
        VACATION_TYPE_NAME,
        "Заявка на ежегодный оплачиваемый отпуск",
    )
    _get_or_create_field(
        session,
        vacation,
        code="date_from",
        name="Дата начала",
        data_type=FieldDataType.DATE,
        required=True,
        order_no=1,
    )
    _get_or_create_field(
        session,
        vacation,
        code="date_to",
        name="Дата окончания",
        data_type=FieldDataType.DATE,
        required=True,
        order_no=2,
    )
    _get_or_create_field(
        session,
        vacation,
        code="comment",
        name="Комментарий",
        data_type=FieldDataType.TEXT,
        required=False,
        order_no=3,
    )
    _ensure_route_with_approver(session, vacation, approver)

    certificate = _get_or_create_request_type(
        session,
        CERTIFICATE_TYPE_NAME,
        "Заявка на кадровую справку",
    )
    _get_or_create_field(
        session,
        certificate,
        code="certificate_kind",
        name="Вид справки",
        data_type=FieldDataType.CATALOG,
        required=True,
        order_no=1,
        dictionary=dictionary,
    )
    _get_or_create_field(
        session,
        certificate,
        code="note",
        name="Примечание",
        data_type=FieldDataType.TEXT,
        required=False,
        order_no=2,
    )
    _ensure_route_with_approver(session, certificate, approver)


def _print_summary(session: Session) -> None:
    role_count = len(session.scalars(select(Role)).all())
    user_count = len(session.scalars(select(User)).all())
    type_count = len(session.scalars(select(RequestType)).all())
    print(
        "Seed complete: "
        f"{role_count} roles, {user_count} users, {type_count} request types "
        f"({VACATION_TYPE_NAME}, {CERTIFICATE_TYPE_NAME})."
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
