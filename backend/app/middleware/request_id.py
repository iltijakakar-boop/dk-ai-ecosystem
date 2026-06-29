import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging.logger import correlation_id_ctx

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that captures or generates a correlation ID for tracking
    each API request round-trip, exposing it in outgoing response headers.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        # Resolve from X-Correlation-ID or X-Request-ID headers
        correlation_id = request.headers.get("X-Correlation-ID") or request.headers.get("X-Request-ID")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Set ContextVar value for correlation logging
        token = correlation_id_ctx.set(correlation_id)
        
        try:
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id
            return response
        finally:
            # Revert/Reset ContextVar after ASGI request lifecycle finished
            correlation_id_ctx.reset(token)
