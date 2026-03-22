"""Structured logging configuration for geo-post-mcp server."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import structlog


def setup_logging(level: int = logging.INFO, log_file: str = "") -> None:
    """Configure structured JSON logging via structlog.

    Args:
        level: Logging level (default INFO).
        log_file: Path to a log file. If empty, logs go to stderr only.
    """
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_output = open(log_path, "a")  # noqa: SIM115
    else:
        log_output = sys.stderr

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=log_output),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=log_output,
        level=level,
    )
