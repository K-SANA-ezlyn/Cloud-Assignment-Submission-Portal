"""
logging_middleware.py — request logging (observability layer).

In cloud deployments this is what feeds CloudWatch / Cloud Logging /
Render logs. Every request is logged with method, path, status and
latency — the raw material for dashboards, alerts and audit trails.
"""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("portal.http")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("UNHANDLED ERROR %s %s", request.method, request.url.path)
            raise
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %s (%.1f ms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
