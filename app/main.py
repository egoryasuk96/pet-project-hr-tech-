"""FastAPI application entrypoint for Employee Service."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import AppError

logger = logging.getLogger(__name__)

_APP_DIR = Path(__file__).resolve().parent
_WEB_DIR = _APP_DIR / "web"
_STATIC_DIR = _APP_DIR / "static"

# Exact HTML paths that do not collide with Target API routes.
_HTML_EXACT = {
    "/login": "login.html",
    "/requests/create": "request-create-select.html",
}

# Colliding with API GET /requests and GET /requests/{id} — HTML only when Accept prefers it.
_DETAIL_RE = re.compile(r"^/requests/(\d+)/?$")
_HTML_ACCEPT_EXACT = {
    "/requests": "requests.html",
    "/notifications": "notifications.html",
}


def _error_body(error_code: str, message: str, details: dict | None = None) -> dict:
    """Target nested envelope (ADR-ERR-03)."""
    return {
        "error": {
            "code": error_code,
            "message": message,
            "details": details or {},
        }
    }


def _wants_html(request: Request) -> bool:
    """True for browser navigation; false for apiFetch (Accept: application/json)."""
    accept = (request.headers.get("accept") or "").lower()
    if "text/html" not in accept:
        return False
    json_pos = accept.find("application/json")
    if json_pos == -1:
        return True
    return accept.find("text/html") < json_pos


def _html_page_for_path(path: str, *, accept_negotiated: bool) -> str | None:
    if path in _HTML_EXACT:
        return _HTML_EXACT[path]
    if accept_negotiated:
        if path in _HTML_ACCEPT_EXACT:
            return _HTML_ACCEPT_EXACT[path]
        if _DETAIL_RE.match(path):
            return "request-detail.html"
    return None


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        description="Employee Service Core API (Stage 5.3). JWT access token, no refresh tokens.",
        version="0.3.0",
    )

    # HTML-only page routes registered before API so /requests/create does not
    # fall through to GET /requests/{request_id} (API path param is untyped in router).
    @application.get("/login", include_in_schema=False)
    def login_page() -> FileResponse:
        return FileResponse(_WEB_DIR / "login.html")

    @application.get("/requests/create", include_in_schema=False)
    def request_create_page() -> FileResponse:
        return FileResponse(_WEB_DIR / "request-create-select.html")

    application.include_router(api_router)
    application.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    @application.middleware("http")
    async def serve_html_when_accepted(request: Request, call_next) -> Response:
        """Serve UI pages for browser Accept: text/html without shadowing JSON API."""
        if request.method == "GET" and _wants_html(request):
            page = _html_page_for_path(request.url.path, accept_negotiated=True)
            if page is not None:
                return FileResponse(_WEB_DIR / page)
        return await call_next(request)

    @application.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/login", status_code=307)

    @application.get("/my-requests", include_in_schema=False)
    def my_requests_redirect() -> RedirectResponse:
        return RedirectResponse(url="/requests", status_code=307)

    @application.get("/my-requests/{request_id:int}", include_in_schema=False)
    def my_request_detail_redirect(request_id: int) -> RedirectResponse:
        return RedirectResponse(url=f"/requests/{request_id}", status_code=307)

    @application.get("/my-notifications", include_in_schema=False)
    def my_notifications_redirect() -> RedirectResponse:
        return RedirectResponse(url="/notifications", status_code=307)

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
