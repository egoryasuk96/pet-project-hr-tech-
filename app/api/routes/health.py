"""Infrastructure health-check endpoint (not part of Baseline OpenAPI)."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Return process liveness. Does not query PostgreSQL."""
    return {"status": "ok"}
