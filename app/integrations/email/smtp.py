"""SMTP email sender (stdlib smtplib, run via ``asyncio.to_thread``).

Avoiding aiosmtplib keeps the dependency footprint small. The blocking call
happens off the event loop so we don't stall the API.
"""
from __future__ import annotations

import asyncio
import logging
import smtplib
import ssl
import uuid
from email.message import EmailMessage as MIMEMessage

from app.integrations.email.base import EmailMessage, EmailSender, SendResult

logger = logging.getLogger(__name__)


class SMTPEmailSender(EmailSender):
    provider = "smtp"

    def __init__(
        self,
        host: str,
        port: int = 587,
        user: str | None = None,
        password: str | None = None,
        use_tls: bool = True,
        default_from: str | None = None,
    ) -> None:
        if not host:
            raise ValueError("SMTPEmailSender requires a host")
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.use_tls = use_tls
        self.default_from = default_from

    def _build_mime(self, message: EmailMessage) -> MIMEMessage:
        mime = MIMEMessage()
        mime["Subject"] = message.subject
        mime["From"] = message.from_ or self.default_from or (self.user or "")
        mime["To"] = message.to
        if message.cc:
            mime["Cc"] = ", ".join(message.cc)
        if message.reply_to:
            mime["Reply-To"] = message.reply_to
        mime.set_content(message.body or "")
        if message.html:
            mime.add_alternative(message.html, subtype="html")
        return mime

    def _send_sync(self, mime: MIMEMessage, recipients: list[str]) -> None:
        if self.use_tls:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.host, self.port, timeout=15) as smtp:
                smtp.starttls(context=context)
                if self.user:
                    smtp.login(self.user, self.password or "")
                smtp.send_message(mime, to_addrs=recipients)
        else:
            with smtplib.SMTP(self.host, self.port, timeout=15) as smtp:
                if self.user:
                    smtp.login(self.user, self.password or "")
                smtp.send_message(mime, to_addrs=recipients)

    async def send(self, message: EmailMessage) -> SendResult:
        if not message.to:
            return SendResult(
                success=False, provider=self.provider, error="missing recipient"
            )
        mime = self._build_mime(message)
        recipients = [message.to, *message.cc, *message.bcc]
        try:
            await asyncio.to_thread(self._send_sync, mime, recipients)
        except Exception as exc:
            logger.warning("SMTP send failed: %s", exc)
            return SendResult(
                success=False, provider=self.provider, error=f"{type(exc).__name__}: {exc}"
            )
        return SendResult(
            success=True,
            message_id=f"smtp_{uuid.uuid4().hex[:12]}",
            provider=self.provider,
        )

    async def close(self) -> None:
        # smtplib opens a fresh connection per send so there is nothing to release.
        return None


__all__ = ["SMTPEmailSender"]
