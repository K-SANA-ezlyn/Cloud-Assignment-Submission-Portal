"""
rate_limit.py — API rate limiting middleware (cloud-security control).

Protects auth and upload endpoints from brute-force and abuse, mirroring
what an API Gateway / WAF enforces in a production cloud architecture.

Implementation: in-memory sliding window per client IP.
  * good enough for a demo / single-instance deployment
  * horizontally scaled deployments would use Redis or gateway-level
    limiting instead (documented in docs/scalability.md)

Disabled automatically when ENVIRONMENT=test.
"""

import threading
import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    LIMITS: dict[str, int] = {
        "/api/auth/login": 10,
        "/api/auth/register": 10,
    }
    DEFAULT_PER_MINUTE = 120        # general API budget per IP
    WINDOW_SECONDS = 60

    def __init__(self, app):
        super().__init__(app)
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    async def dispatch(self, request: Request, call_next):
        if settings.ENVIRONMENT == "test":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        limit = self.LIMITS.get(request.url.path, self.DEFAULT_PER_MINUTE)
        now = time.monotonic()

        with self._lock:
            window = self._hits[(client_ip, request.url.path)]
            while window and now - window[0] > self.WINDOW_SECONDS:
                window.popleft()
            if len(window) >= limit:
                retry_after = int(self.WINDOW_SECONDS - (now - window[0])) + 1
                return JSONResponse(
                    status_code=429,
                    content={"detail": f"Rate limit exceeded. Retry in {retry_after}s."},
                    headers={"Retry-After": str(retry_after)},
                )
            window.append(now)

        return await call_next(request)
