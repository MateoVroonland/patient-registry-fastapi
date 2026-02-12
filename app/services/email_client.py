from __future__ import annotations

from abc import ABC, abstractmethod
from asyncio import to_thread
from email.message import EmailMessage
from smtplib import SMTP, SMTP_SSL

from app.core.logging import get_logger

logger = get_logger(__name__)

SMTP_SSL_PORT = 465
SMTP_TIMEOUT_SECONDS = 10


class EmailClient(ABC):
    @abstractmethod
    async def send_email(
        self,
        *,
        to_email: str,
        to_name: str,
        subject: str,
        body: str,
    ) -> None: ...


class MailtrapSmtpEmailClient(EmailClient):
    def __init__(  # noqa: PLR0913
        self,
        *,
        host: str,
        port: int,
        username: str,
        password: str,
        from_email: str,
        from_name: str,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._from_email = from_email
        self._from_name = from_name

    async def send_email(
        self,
        *,
        to_email: str,
        to_name: str,
        subject: str,
        body: str,
    ) -> None:
        try:
            await to_thread(
                self._send_email_sync,
                to_email=to_email,
                to_name=to_name,
                subject=subject,
                body=body,
            )
        except Exception:
            logger.exception("Failed to send SMTP confirmation email to '%s'.", to_email)

    def _send_email_sync(
        self,
        *,
        to_email: str,
        to_name: str,
        subject: str,
        body: str,
    ) -> None:
        message = EmailMessage()
        message["From"] = f"{self._from_name} <{self._from_email}>"
        message["To"] = f"{to_name} <{to_email}>"
        message["Subject"] = subject
        message.set_content(body)

        smtp_factory = SMTP_SSL if self._port == SMTP_SSL_PORT else SMTP
        with smtp_factory(self._host, self._port, timeout=SMTP_TIMEOUT_SECONDS) as smtp:
            if self._port != SMTP_SSL_PORT:
                smtp.starttls()
            smtp.login(self._username, self._password)
            smtp.send_message(message)


class NoopEmailClient(EmailClient):
    async def send_email(
        self,
        *,
        to_email: str,
        to_name: str,
        subject: str,
        body: str,
    ) -> None:
        logger.info(
            "Noop email client - skipping send to '%s' (%s) with subject '%s' and body length %s.",
            to_name,
            to_email,
            subject,
            len(body),
        )
