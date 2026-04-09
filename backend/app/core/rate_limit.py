"""
CryptoGuard-R - Rate Limiting Middleware
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.security import check_rate_limit
from app.core.logging import get_logger

logger = get_logger("rate_limit")


def get_client_id(request: Request) -> str:
    """Extract client identifier (IP) from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host or "unknown"
    return "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Basic rate limiting per client IP."""

    async def dispatch(self, request: Request, call_next):
        client_id = get_client_id(request)
        allowed, msg = check_rate_limit(client_id)
        if not allowed:
            logger.warning("Rate limit exceeded for %s", client_id)
            return JSONResponse(
                status_code=429,
                content={"detail": msg, "code": "RATE_LIMIT_EXCEEDED"},
            )
        return await call_next(request)
