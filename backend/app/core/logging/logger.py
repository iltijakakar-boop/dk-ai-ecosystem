import contextvars
import logging
from typing import Optional

# Thread-safe ContextVar to hold correlation ID scoped to the current ASGI request
# context
correlation_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "correlation_id", default=None
)

# Ecosystem parent logger
logger = logging.getLogger("dk_ai_ecosystem")
