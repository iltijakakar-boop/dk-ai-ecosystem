import json
import logging
from datetime import datetime
from app.core.logging.logger import correlation_id_ctx

class JSONFormatter(logging.Formatter):
    """
    Structured JSON logger formatter. Appends request correlation IDs and stack traces.
    """
    def format(self, record: logging.LogRecord) -> str:
        correlation_id = correlation_id_ctx.get()
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


class ConsoleFormatter(logging.Formatter):
    """
    Standard text formatter designed for local console developments.
    """
    def format(self, record: logging.LogRecord) -> str:
        correlation_id = correlation_id_ctx.get()
        cid_str = f" [cid:{correlation_id}]" if correlation_id else ""
        asctime = self.formatTime(record, self.datefmt)
        # Format: 2026-06-29 22:38:00 [INFO] [cid:uuid] dk_ai_ecosystem: message content
        return f"{asctime} [{record.levelname}]{cid_str} {record.name}: {record.getMessage()}"
