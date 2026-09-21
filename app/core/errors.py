"""Domain errors mapped to the Error Matrix envelope (ADR-ERR-01)."""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Business or auth error with a stable error_code and HTTP status."""

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
    return AppError(
        "ERR_INVALID_CREDENTIALS",
        "Неверный логин или пароль",
        401,
    )


def unauthorized() -> AppError:
    return AppError(
        "ERR_UNAUTHORIZED",
        "Требуется аутентификация",
        401,
    )


def forbidden() -> AppError:
    return AppError(
        "ERR_FORBIDDEN",
        "Недостаточно прав для выполнения операции",
        403,
    )


def forbidden_approval() -> AppError:
    return AppError(
        "ERR_FORBIDDEN_APPROVAL",
        "Нет полномочий на заявку",
        403,
    )


def not_found() -> AppError:
    return AppError(
        "ERR_NOT_FOUND",
        "Объект не найден",
        404,
    )


def validation(details: dict[str, Any] | None = None) -> AppError:
    return AppError(
        "ERR_VALIDATION",
        "Проверьте корректность заполнения полей",
        422,
        details,
    )


def inactive_type() -> AppError:
    return AppError(
        "ERR_INACTIVE_TYPE",
        "Этот тип заявки недоступен",
        409,
    )


def invalid_state() -> AppError:
    return AppError(
        "ERR_INVALID_STATE",
        "Действие недоступно для текущего статуса",
        409,
    )


def task_done() -> AppError:
    return AppError(
        "ERR_TASK_DONE",
        "Задача уже обработана",
        409,
    )


def route_config() -> AppError:
    return AppError(
        "ERR_ROUTE_CONFIG",
        "Маршрут согласования настроен некорректно",
        409,
    )
