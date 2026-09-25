"""
app.py — FastAPI application factory.

Cloud concepts wired here:
  * CORS allowlist  (browser security between SPA and API)
  * request logging (observability -> feeds Render/CloudWatch logs)
  * rate limiting   (abuse protection, like an API gateway)
  * error handlers  (graceful failure responses)
  * routers         (the REST API surface)
  * DB bootstrap    (create tables on startup for local/demo use)
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.middleware.error_handlers import register_error_handlers
from backend.middleware.logging_middleware import RequestLoggingMiddleware
from backend.middleware.rate_limit import RateLimitMiddleware
from backend.routes.assignment_routes import router as assignment_router
from backend.routes.auth_routes import router as auth_router
from backend.routes.course_routes import router as course_router
from backend.routes.dashboard_routes import router as dashboard_router
from backend.routes.health_routes import router as health_router
from backend.routes.submission_routes import router as submission_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("portal.app")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        description=(
            "REST API for the Cloud-Based Student Assignment Submission & "
            "Feedback Portal — role-based auth, cloud database, object "
            "storage, assignment management, grading and feedback."
        ),
    )

    # ---- CORS: only origins in the allowlist may call this API ----
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---- Observability + protection middleware ----
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)

    # ---- Error handling ----
    register_error_handlers(app)

    # ---- REST API routers ----
    app.include_router(auth_router)
    app.include_router(course_router)
    app.include_router(assignment_router)
    app.include_router(submission_router)
    app.include_router(dashboard_router)
    app.include_router(health_router)

    # ---- Create tables on startup (local/demo convenience) ----
    @app.on_event("startup")
    def _bootstrap() -> None:
        from backend.database import Base, engine
        import backend.models  # noqa: F401 — register all models

        Base.metadata.create_all(bind=engine)
        logger.info(
            "Portal API started | env=%s | storage=%s | auth=%s | db=%s",
            settings.ENVIRONMENT,
            settings.STORAGE_PROVIDER,
            settings.AUTH_PROVIDER,
            settings.DATABASE_URL.split("://")[0],
        )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.app:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
    )
