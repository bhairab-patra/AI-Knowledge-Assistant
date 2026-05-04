"""Logger helper - thin wrapper exposing structlog loggers to modules."""
from config.logging_config import configure_logging, get_logger

__all__ = ["configure_logging", "get_logger"]
