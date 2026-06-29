import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging.logger import logger
from app.monitoring.metrics import metrics_registry


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware logging incoming HTTP request paths, HTTP verbs, response status codes,
    durations, and updating active telemetry counters in the metrics registry.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        method = request.method
        path = request.url.path

        logger.info(f"Request started: {method} {path}")

        # Increment total requests counter
        metrics_registry.increment_request()

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            # Record telemetry data
            metrics_registry.record_response_time(duration_ms)
            if response.status_code >= 400:
                metrics_registry.increment_error()

            logger.info(
                f"Request finished: {method} {path} - status={response.status_code} - duration={duration_ms:.2f}ms"
            )
            return response
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            metrics_registry.increment_error()
            logger.error(
                f"Request failed: {method} {path} - error={str(e)} - duration={duration_ms:.2f}ms"
            )
            raise e
