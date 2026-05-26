"""Console (in-process) email sender.

Used in dev and tests. Records every send in ``sent`` so tests can assert
behaviour without a real SMTP server.
"""
from __future__ import annotations

import logging
import uuid

from app.integrations.email.base import EmailMessage, EmailSender, SendResult

logger = logging.getLogger(__name__)


class ConsoleEmailSender(EmailSender):
    provider = "console"

    def __init__(self) -> None:
        self.sent: list[EmailMessage] = []

    async def send(self, message: EmailMessage) -> SendResult:
        message_id = f"console_{uuid.uuid4().hex[:12]}"
        self.sent.append(message)
        logger.info(
            "console email -> %s | subject=%r | body_chars=%d",
            message.to,
            message.subject,
            len(message.body or ""),
        )
        return SendResult(
            success=True, message_id=message_id, provider=self.provider
        )

    async def close(self) -> None:
        return None


__all__ = ["ConsoleEmailSender"]
