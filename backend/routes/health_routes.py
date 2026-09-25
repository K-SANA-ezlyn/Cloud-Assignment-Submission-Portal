"""
health_routes.py — observability endpoints (used by monitoring/UptimeRobot).

GET /api/health         app process is alive
GET /api/health/db      cloud database probe
GET /api/health/storage cloud object-storage probe
"""

from fastapi import APIRouter, Response, status

from backend.cloud.database_service import database_health
from backend.cloud.storage_service import get_storage_provider
from backend.config import settings

router = APIRouter(tags=["health"])


@router.get("/api/health")
def health():
    """Liveness probe — process up and serving requests."""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "storage_provider": settings.STORAGE_PROVIDER,
    }


@router.get("/api/health/db")
def health_db(response: Response):
    """Readiness probe for the cloud database (SQLite locally)."""
    ok, detail = database_health()
    response.status_code = status.HTTP_200_OK if ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ok" if ok else "error", "detail": detail}


@router.get("/api/health/storage")
def health_storage(response: Response):
    """Readiness probe for the object storage backend."""
    ok = get_storage_provider().health_check()
    response.status_code = status.HTTP_200_OK if ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": "ok" if ok else "error",
        "provider": settings.STORAGE_PROVIDER,
    }
