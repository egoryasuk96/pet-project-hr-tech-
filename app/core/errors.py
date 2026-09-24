"""Domain errors with Target codes (ADR-ERR-03 nested envelope)."""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Business or auth error with a stable Target code and HTTP status."""

    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details if details is not None else {}


def invalid_credentials() -> AppError:
    return AppError("INVALID_CREDENTIALS", "Неверный логин или пароль", 401)


def unauthorized() -> AppError:
    return AppError("UNAUTHORIZED", "Требуется аутентификация", 401)


def forbidden() -> AppError:
    return AppError("FORBIDDEN", "Недостаточно прав для выполнения операции", 403)


def forbidden_approval(message: str | None = None) -> AppError:
    return AppError(
        "FORBIDDEN_APPROVAL",
        message or "Вы не можете выполнить действие по этой задаче",
        403,
    )


def not_found(message: str | None = None) -> AppError:
    return AppError("NOT_FOUND", message or "Объект не найден", 404)


def validation(
    details: dict[str, Any] | None = None,
    message: str | None = None,
) -> AppError:
    return AppError(
        "VALIDATION",
        message or "Проверьте корректность заполнения полей",
        422,
        details,
    )


def inactive_type() -> AppError:
    return AppError("INACTIVE_TYPE", "Этот тип заявки недоступен", 409)


def invalid_state() -> AppError:
    return AppError(
        "INVALID_STATE",
        "Действие недоступно для текущего статуса",
        409,
    )


def request_action_not_allowed(message: str | None = None) -> AppError:
    return AppError(
        "REQUEST_ACTION_NOT_ALLOWED",
        message or "Действие недоступно для текущего статуса",
        409,
    )


def task_done() -> AppError:
    return AppError("TASK_DONE", "Задача уже обработана", 409)


def route_config() -> AppError:
    return AppError(
        "ROUTE_CONFIG",
        "Маршрут согласования настроен некорректно",
        409,
    )


# --- Action Engine helpers (canonical codes; names kept for call-site clarity) ---


def request_not_found() -> AppError:
    return not_found("Заявка не найдена")


def action_not_found() -> AppError:
    return not_found("Действие не найдено")


def action_not_allowed() -> AppError:
    return request_action_not_allowed(
        "Действие недоступно для заявки в текущем статусе или роли"
    )


def self_approval_forbidden() -> AppError:
    return forbidden_approval("Инициатор не может согласовать собственную заявку")


def approval_task_not_found() -> AppError:
    return forbidden_approval(
        "Нет активной задачи согласования для текущего пользователя"
    )


def comment_required() -> AppError:
    return validation(message="Комментарий обязателен для этого действия")


def invalid_request_state() -> AppError:
    return request_action_not_allowed(
        "Состояние заявки не позволяет выполнить действие"
    )
