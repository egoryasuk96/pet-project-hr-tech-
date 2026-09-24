"""FastAPI application entrypoint for Employee Service."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import AppError

logger = logging.getLogger(__name__)

_APP_DIR = Path(__file__).resolve().parent
_WEB_DIR = _APP_DIR / "web"
_STATIC_DIR = _APP_DIR / "static"


def _error_body(error_code: str, message: str, details: dict | None = None) -> dict:
    """Target nested envelope (ADR-ERR-03)."""
    return {
        "error": {
            "code": error_code,
            "message": message,
            "details": details or {},
        }
    }


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        description="Employee Service Core API (Stage 5.3). JWT access token, no refresh tokens.",
        version="0.3.0",
    )
    application.include_router(api_router)
    application.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    @application.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/login", status_code=307)

    @application.get("/login", include_in_schema=False)
    def login_page() -> FileResponse:
        return FileResponse(_WEB_DIR / "login.html")

    @application.get("/my-requests", include_in_schema=False)
    def my_requests_page() -> FileResponse:
        return FileResponse(_WEB_DIR / "requests.html")

    @application.get("/my-requests/{request_id:int}", include_in_schema=False)
    def request_detail_page(request_id: int) -> FileResponse:
        return FileResponse(_WEB_DIR / "request-detail.html")

    @application.get("/my-notifications", include_in_schema=False)
    def notifications_page() -> FileResponse:
        return FileResponse(_WEB_DIR / "notifications.html")

    @application.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.error_code, exc.message, exc.details),
        )

    @application.exception_handler(RequestValidationError)
    async def validation_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_error_body(
                "VALIDATION",
                "Проверьте корректность заполнения полей",
                {"errors": exc.errors()},
            ),
        )

    @application.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        if isinstance(exc, StarletteHTTPException):
            return await http_exception_handler(request, exc)
        logger.exception("Unhandled error")
        return JSONResponse(
            status_code=500,
            content=_error_body(
                "INTERNAL",
                "Произошла внутренняя ошибка. Попробуйте позже",
            ),
        )

    return application


app = create_app()
