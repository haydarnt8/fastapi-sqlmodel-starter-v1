"""
Logging Configuration

This module sets up structured logging for the application.

Why structured logging?
- Easy to parse and analyze
- Better integration with log aggregation tools (ELK, Datadog, etc.)
- Consistent log format across the application
- Ability to add context (request_id, user_id, etc.)
- JSON format for machine readability

Log Levels:
- DEBUG: Detailed information for debugging
- INFO: General informational messages
- WARNING: Warning messages (something unexpected but handled)
- ERROR: Error messages (something failed)
- CRITICAL: Critical errors (system is unusable)
"""

import logging
import sys
from typing import Any, Dict
from pythonjsonlogger import jsonlogger

from app.core.config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter that adds standard fields to every log.

    Adds:
    - environment: dev/staging/prod
    - app_name: Application name
    - Any additional fields passed to the logger
    """

    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any],
    ) -> None:
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)

        # Add standard fields
        log_record["environment"] = settings.ENVIRONMENT
        log_record["app_name"] = settings.APP_NAME
        log_record["level"] = record.levelname
        log_record["logger_name"] = record.name

        # Add request context if available (set by middleware)
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_record["user_id"] = record.user_id


def setup_logging() -> None:
    """
    Configure application logging.

    Sets up:
    - Log level from settings
    - JSON or text format
    - Console and/or file output
    - Custom formatter with additional fields
    """
    # Get root logger
    root_logger = logging.getLogger()

    # Clear existing handlers
    root_logger.handlers.clear()

    # Set log level
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root_logger.setLevel(log_level)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Choose formatter based on settings
    if settings.LOG_FORMAT.lower() == "json":
        # JSON formatter for production
        formatter = CustomJsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s",
            rename_fields={"timestamp": "asctime"},
        )
    else:
        # Human-readable formatter for development
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Add file handler if LOG_FILE is set
    if settings.LOG_FILE:
        file_handler = logging.FileHandler(settings.LOG_FILE)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # Log startup message
    root_logger.info(
        "Logging configured",
        extra={
            "log_level": settings.LOG_LEVEL,
            "log_format": settings.LOG_FORMAT,
            "environment": settings.ENVIRONMENT,
        },
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        logging.Logger: Logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("User logged in", extra={"user_id": 123})
    """
    return logging.getLogger(name)


# Create a logger for this module
logger = get_logger(__name__)
