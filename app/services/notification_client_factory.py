from __future__ import annotations

from collections.abc import Callable, Sequence

from app.core.settings import Settings
from app.services.notification_client import (
    MailtrapSmtpNotificationClient,
    NoopNotificationClient,
    NotificationClient,
    SmtpEmailConfig,
)

type NotificationClientBuilder = Callable[[Settings], NotificationClient | None]


def _smtp_email_config_from_settings(settings: Settings) -> SmtpEmailConfig | None:
    host = settings.mail_host
    port = settings.mail_port
    username = settings.mail_username
    password = settings.mail_password
    from_email = settings.mail_from_email
    from_name = settings.mail_from_name

    if (
        host is None
        or port is None
        or username is None
        or password is None
        or from_email is None
        or from_name is None
    ):
        return None

    return SmtpEmailConfig(
        host=host,
        port=port,
        username=username,
        password=password,
        from_email=from_email,
        from_name=from_name,
    )


def _build_mailtrap_smtp_client(settings: Settings) -> NotificationClient | None:
    config = _smtp_email_config_from_settings(settings=settings)
    if config is None:
        return None
    return MailtrapSmtpNotificationClient(config=config)


DEFAULT_NOTIFICATION_CLIENT_BUILDERS: tuple[NotificationClientBuilder, ...] = (
    _build_mailtrap_smtp_client,
)


def create_notification_client(
    settings: Settings,
    *,
    builders: Sequence[NotificationClientBuilder] = DEFAULT_NOTIFICATION_CLIENT_BUILDERS,
) -> NotificationClient:
    for builder in builders:
        client = builder(settings)
        if client is not None:
            return client
    return NoopNotificationClient()
