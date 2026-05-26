"""Structured JSON logging with PII redaction.

The redaction filter is attached at the root level + on every handler so
sub-loggers and downstream handlers can't accidentally bypass it.
"""
from __future__ import annotations

import logging
import sys

from pythonjsonlogger import jsonlogger

from app.observability.redaction import PIIRedactionFilter


def setup_logging() -> None:
    """Configure JSON logging + install PII redaction."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    json_formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s"
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(json_formatter)

    redaction = PIIRedactionFilter()
    handler.addFilter(redaction)

    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.addFilter(redaction)

    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("opentelemetry").setLevel(logging.WARNING)


__all__ = ["setup_logging"]
