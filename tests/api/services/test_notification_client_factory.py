from app.core.settings import Settings
from app.services.notification_client import MailtrapSmtpNotificationClient, NoopNotificationClient
from app.services.notification_client_factory import create_notification_client


def test_create_notification_client_returns_noop_when_smtp_settings_are_incomplete() -> None:
    settings = Settings(
        mail_host="smtp.mailtrap.test",
        mail_port=587,
        mail_username="user",
        mail_password=None,
        mail_from_email="noreply@example.test",
        mail_from_name="Patient Registry",
    )

    client = create_notification_client(settings)
    assert isinstance(client, NoopNotificationClient)


def test_create_notification_client_returns_mailtrap_client_when_smtp_settings_are_complete() -> None:
    settings = Settings(
        mail_host="smtp.mailtrap.test",
        mail_port=587,
        mail_username="user",
        mail_password="pass",
        mail_from_email="noreply@example.test",
        mail_from_name="Patient Registry",
    )

    client = create_notification_client(settings)
    assert isinstance(client, MailtrapSmtpNotificationClient)
