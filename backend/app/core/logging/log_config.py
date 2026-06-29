import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from app.config.settings import settings
from app.core.logging.formatter import ConsoleFormatter, JSONFormatter


def setup_logging(environment: str = "development") -> None:
    """
    Sets up global logging levels, formats, console streams, and rotating file outputs.
    """
    # Parse logging level
    level_str = settings.LOG_LEVEL.upper()
    level = getattr(logging, level_str, logging.INFO)

    # Determine standard formatter
    use_json = settings.ENABLE_JSON_LOGGING or settings.LOG_FORMAT.upper() == "JSON"
    formatter = JSONFormatter() if use_json else ConsoleFormatter()

    handlers = []

    # 1. Console Stream Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)

    # 2. File rotation logging handler (if enabled)
    if settings.ENABLE_FILE_LOGGING:
        log_dir = "logs"
        try:
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "app.log")
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10 MB per log file
                backupCount=5,  # Keep up to 5 rotated files
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)
        except Exception as e:
            # Fallback to printing if permission checks or folders fail
            print(f"Failed to initialize file logging handler: {e}", file=sys.stderr)

    # Apply configured handlers to the root logger
    root_logger = logging.getLogger()
    root_logger.handlers = []
    for h in handlers:
        root_logger.addHandler(h)

    root_logger.setLevel(level)
