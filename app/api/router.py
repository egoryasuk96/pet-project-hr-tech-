"""Aggregate API routers for the FastAPI application."""

from fastapi import APIRouter

from app.api.routes import approval_tasks, auth, health, me, notifications, request_types, requests

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(me.router)
api_router.include_router(request_types.router)
api_router.include_router(requests.router)
api_router.include_router(approval_tasks.router)
api_router.include_router(notifications.router)
