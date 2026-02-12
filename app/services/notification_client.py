from __future__ import annotations

from abc import ABC, abstractmethod
from asyncio import to_thread
from dataclasses import dataclass
from email.message import EmailMessage
from smtplib import SMTP, SMTP_SSL

from app.core.logging import get_logger

logger = get_logger(__name__)

SMTP_SSL_PORT = 465
SMTP_TIMEOUT_SECONDS = 10
DEFAULT_EMAIL_SUBJECT = "Notification"


@dataclass(slots=True, frozen=True)
class NotificationMessage:
    recipient: str
    body: str
    subject: str | None = None
    recipient_name: str | None = None


@dataclass(slots=True, frozen=True)
class SmtpEmailConfig:
    host: str
    port: int
    username: str
    password: str
    from_email: str
    from_name: str


class NotificationClient(ABC):
    @abstractmethod
    async def send_notification(self, *, message: NotificationMessage) -> None: ...


class MailtrapSmtpNotificationClient(NotificationClient):
    def __init__(self, config: SmtpEmailConfig) -> None:
        self._config = config

    async def send_notification(self, *, message: NotificationMessage) -> None:
        try:
            await to_thread(self._send_notification_sync, message=message)
        except Exception:
            logger.exception("Failed to send SMTP notification to '%s'.", message.recipient)

    def _send_notification_sync(self, *, message: NotificationMessage) -> None:
        email_message = EmailMessage()
        email_message["From"] = f"{self._config.from_name} <{self._config.from_email}>"
        if message.recipient_name:
            email_message["To"] = f"{message.recipient_name} <{message.recipient}>"
        else:
            email_message["To"] = message.recipient
        email_message["Subject"] = message.subject or DEFAULT_EMAIL_SUBJECT
        email_message.set_content(message.body)

        smtp_factory = SMTP_SSL if self._config.port == SMTP_SSL_PORT else SMTP
        with smtp_factory(self._config.host, self._config.port, timeout=SMTP_TIMEOUT_SECONDS) as smtp:
            if self._config.port != SMTP_SSL_PORT:
                smtp.starttls()
            smtp.login(self._config.username, self._config.password)
            smtp.send_message(email_message)


class NoopNotificationClient(NotificationClient):
    async def send_notification(self, *, message: NotificationMessage) -> None:
        logger.info(
            "Noop notification client - skipping send to '%s' with subject '%s'.",
            message.recipient,
            message.subject or DEFAULT_EMAIL_SUBJECT,
        )
