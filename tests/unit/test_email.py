"""Email sender behaviour and factory selection."""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_console_sender_records_and_succeeds():
    from app.integrations.email.base import EmailMessage
    from app.integrations.email.console import ConsoleEmailSender

    sender = ConsoleEmailSender()
    result = await sender.send(
        EmailMessage(to="lead@target.test", subject="Hi", body="hello there")
    )
    assert result.success is True
    assert result.provider == "console"
    assert result.message_id and result.message_id.startswith("console_")
    assert len(sender.sent) == 1
    assert sender.sent[0].to == "lead@target.test"


def test_factory_default_is_console(monkeypatch):
    from app.integrations.email import factory
    from app.integrations.email.console import ConsoleEmailSender

    monkeypatch.setattr(factory.settings, "EMAIL_PROVIDER", "console")
    assert isinstance(factory.get_email_sender(), ConsoleEmailSender)


def test_factory_smtp_falls_back_when_host_missing(monkeypatch):
    from app.integrations.email import factory
    from app.integrations.email.console import ConsoleEmailSender

    monkeypatch.setattr(factory.settings, "EMAIL_PROVIDER", "smtp")
    monkeypatch.setattr(factory.settings, "SMTP_HOST", "")
    assert isinstance(factory.get_email_sender(), ConsoleEmailSender)


def test_factory_smtp_picks_smtp_when_configured(monkeypatch):
    from app.integrations.email import factory
    from app.integrations.email.smtp import SMTPEmailSender

    monkeypatch.setattr(factory.settings, "EMAIL_PROVIDER", "smtp")
    monkeypatch.setattr(factory.settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(factory.settings, "SMTP_PORT", 587)
    monkeypatch.setattr(factory.settings, "SMTP_USER", "u")
    monkeypatch.setattr(factory.settings, "SMTP_PASSWORD", "p")
    monkeypatch.setattr(factory.settings, "SMTP_USE_TLS", True)
    monkeypatch.setattr(factory.settings, "SMTP_FROM", "noreply@example.com")
    sender = factory.get_email_sender()
    assert isinstance(sender, SMTPEmailSender)
    assert sender.host == "smtp.example.com"


@pytest.mark.asyncio
async def test_smtp_sender_handles_transport_failure(monkeypatch):
    """When the underlying smtplib call raises, send() returns success=False."""
    from app.integrations.email.base import EmailMessage
    from app.integrations.email.smtp import SMTPEmailSender

    sender = SMTPEmailSender(host="smtp.example.com", default_from="noreply@x.test")

    def boom(self, mime, recipients):  # noqa: ANN001
        raise RuntimeError("connection refused")

    monkeypatch.setattr(SMTPEmailSender, "_send_sync", boom)
    result = await sender.send(
        EmailMessage(to="lead@target.test", subject="Hi", body="hello")
    )
    assert result.success is False
    assert "connection refused" in (result.error or "")


@pytest.mark.asyncio
async def test_smtp_sender_rejects_missing_recipient():
    from app.integrations.email.base import EmailMessage
    from app.integrations.email.smtp import SMTPEmailSender

    sender = SMTPEmailSender(host="smtp.example.com")
    result = await sender.send(EmailMessage(to="", subject="Hi", body="hello"))
    assert result.success is False
    assert result.error == "missing recipient"
