"""Pick an email sender based on settings.

Defaults to ``ConsoleEmailSender`` so tests and dev environments never
accidentally hit a real SMTP server. Set ``EMAIL_PROVIDER=smtp`` and the
``SMTP_*`` env vars to switch on real delivery.
"""
from __future__ import annotations

import logging

from app.core.config import settings
from app.integrations.email.base import EmailSender
from app.integrations.email.console import ConsoleEmailSender

logger = logging.getLogger(__name__)


def get_email_sender() -> EmailSender:
    provider = (settings.EMAIL_PROVIDER or "console").lower().strip()
    if provider == "smtp":
        if not settings.SMTP_HOST:
            logger.warning(
                "EMAIL_PROVIDER=smtp but SMTP_HOST is empty; falling back to console"
            )
            return ConsoleEmailSender()
        from app.integrations.email.smtp import SMTPEmailSender

        return SMTPEmailSender(
            host=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            user=settings.SMTP_USER or None,
            password=settings.SMTP_PASSWORD or None,
            use_tls=settings.SMTP_USE_TLS,
            default_from=settings.SMTP_FROM,
        )
    if provider != "console":
        logger.warning("Unknown EMAIL_PROVIDER %r — falling back to console", provider)
    return ConsoleEmailSender()


__all__ = ["get_email_sender"]
