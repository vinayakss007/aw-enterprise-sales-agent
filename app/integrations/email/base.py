"""Email-sender protocol and shared types."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class EmailMessage:
    """A simple message body the senders know how to deliver."""

    to: str
    subject: str
    body: str
    from_: str | None = None
    cc: list[str] = field(default_factory=list)
    bcc: list[str] = field(default_factory=list)
    reply_to: str | None = None
    html: str | None = None  # optional HTML alternative


@dataclass
class SendResult:
    """The outcome of a send."""

    success: bool
    message_id: str | None = None
    provider: str = ""
    error: str | None = None


@runtime_checkable
class EmailSender(Protocol):
    provider: str

    async def send(self, message: EmailMessage) -> SendResult: ...

    async def close(self) -> None: ...


__all__ = ["EmailMessage", "EmailSender", "SendResult"]
