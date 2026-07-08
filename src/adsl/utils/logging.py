"""Structured logging configuration for ADSL."""

from __future__ import annotations

import logging

import structlog


def configure_logging(*, log_level: int = logging.INFO) -> None:
    """Configure structlog for JSON-friendly structured output."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str):
    """Return a named structlog logger."""
    return structlog.get_logger(name)