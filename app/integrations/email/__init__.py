"""Email-sender package."""
from app.integrations.email.base import EmailMessage, EmailSender, SendResult
from app.integrations.email.factory import get_email_sender

__all__ = ["EmailMessage", "EmailSender", "SendResult", "get_email_sender"]
