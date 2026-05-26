"""PII redaction for log records.

Installed as a logging filter so it runs against every record on its way to
stdout, regardless of which logger emitted it. The filter rewrites both
``record.msg`` and any string-typed ``record.args``, plus the ``extra=``
fields added by middleware. It deliberately errs on the side of redacting
anything that *looks* like PII rather than parsing each format precisely —
false positives in logs are far cheaper than false negatives.

Patterns covered:
  * Email addresses                      → ``[email]``
  * ``Bearer <token>`` headers           → ``Bearer [REDACTED]``
  * JSON-style ``"password": "..."``     → ``"password":"[REDACTED]"`` (also
    secret/api_key/access_token/authorization)
  * ``key=value`` form fields where      → ``key=[REDACTED]``
    ``key`` is a known secret name
"""
from __future__ import annotations

import logging
import re
from collections.abc import Iterable
from typing import Any

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
BEARER_RE = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._\-]+")
SECRET_KEYS = (
    "password",
    "secret",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "authorization",
    "client_secret",
)
JSON_SECRET_RE = re.compile(
    r'(?i)"(' + "|".join(SECRET_KEYS) + r')"\s*:\s*"[^"]*"'
)
FORM_SECRET_RE = re.compile(
    r"(?i)\b(" + "|".join(SECRET_KEYS) + r")=([^&\s]*)"
)

REDACTED = "[REDACTED]"
EMAIL_PLACEHOLDER = "[email]"

_EXTRA_FIELDS_TO_SCRUB = (
    "path",
    "url",
    "headers",
    "body",
    "message",
)


def redact(text: str) -> str:
    """Apply every redaction pattern to ``text`` and return the result."""
    if not isinstance(text, str) or not text:
        return text
    text = JSON_SECRET_RE.sub(
        lambda m: f'"{m.group(1)}":"{REDACTED}"', text
    )
    text = FORM_SECRET_RE.sub(
        lambda m: f"{m.group(1)}={REDACTED}", text
    )
    text = BEARER_RE.sub("Bearer " + REDACTED, text)
    text = EMAIL_RE.sub(EMAIL_PLACEHOLDER, text)
    return text


def _redact_args(args: Any) -> Any:
    if isinstance(args, tuple):
        return tuple(redact(a) if isinstance(a, str) else a for a in args)
    if isinstance(args, dict):
        return {k: redact(v) if isinstance(v, str) else v for k, v in args.items()}
    return args


class PIIRedactionFilter(logging.Filter):
    """Logging filter that scrubs known PII patterns from records."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            if isinstance(record.msg, str):
                record.msg = redact(record.msg)
            if record.args:
                record.args = _redact_args(record.args)
            for field in _EXTRA_FIELDS_TO_SCRUB:
                value = getattr(record, field, None)
                if isinstance(value, str):
                    setattr(record, field, redact(value))
        except Exception:  # pragma: no cover — never break logging
            pass
        return True


def install_redaction(loggers: Iterable[logging.Logger] | None = None) -> None:
    """Attach a ``PIIRedactionFilter`` to every supplied logger."""
    flt = PIIRedactionFilter()
    for logger in (loggers or [logging.getLogger()]):
        logger.addFilter(flt)
        for handler in getattr(logger, "handlers", []):
            handler.addFilter(flt)


__all__ = [
    "PIIRedactionFilter",
    "install_redaction",
    "redact",
    "EMAIL_PLACEHOLDER",
    "REDACTED",
]
