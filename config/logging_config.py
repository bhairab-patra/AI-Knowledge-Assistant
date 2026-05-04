"""
Centralized structured logging configuration using structlog.

Outputs JSON in production for ingestion by log aggregators (CloudWatch, ELK,
Datadog) and human-friendly colored output during development.
"""
import logging
import sys
from typing import Any, Dict

import structlog

from config.settings import settings


def configure_logging() -> None:
    """Configure structlog for application-wide structured logging."""
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    # NOTE: We avoid `structlog.stdlib.add_logger_name` here because we use
    # PrintLoggerFactory (which yields a `PrintLogger` that has no `.name`
    # attribute). Logger identity is propagated via the `logger` key bound
    # in `get_logger` instead.
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        timestamper,
    ]

    if settings.is_production:
        # JSON renderer for production log aggregation
        renderer: Any = structlog.processors.JSONRenderer()
    else:
        # Colored console renderer for local development
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.LOG_LEVEL)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging to forward to structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL),
    )

    # Reduce noise from chatty third-party loggers
    for noisy_logger in ("botocore", "urllib3", "boto3", "httpx", "httpcore"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a structlog logger pre-bound with a `logger` name field."""
    logger_name = name or __name__
    return structlog.get_logger().bind(logger=logger_name)
