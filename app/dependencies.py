from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.db.session import get_session
from app.repositories.file_repository import FileRepository
from app.repositories.patient_repository import PatientRepository
from app.services.file_storage_service import LocalFileStorageService
from app.services.notification_client import (
    MailtrapSmtpNotificationClient,
    NotificationClient,
    SmtpEmailConfig,
)
from app.services.patient_service import PatientService

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_file_storage_service() -> LocalFileStorageService:
    return LocalFileStorageService()


def get_notification_client() -> NotificationClient:
    if all(
        (
            settings.mail_host,
            settings.mail_port,
            settings.mail_username,
            settings.mail_password,
            settings.mail_from_email,
            settings.mail_from_name,
        ),
    ):
        smtp_email_config = SmtpEmailConfig(
            host=settings.mail_host,
            port=settings.mail_port,
            username=settings.mail_username,
            password=settings.mail_password,
            from_email=settings.mail_from_email,
            from_name=settings.mail_from_name,
        )
        return MailtrapSmtpNotificationClient(config=smtp_email_config)

    raise ValueError("Mailtrap SMTP configuration is not set")


def get_file_repository(session: SessionDep) -> FileRepository:
    return FileRepository(session=session)


def get_patient_repository(session: SessionDep) -> PatientRepository:
    return PatientRepository(session=session)


FileRepositoryDep = Annotated[FileRepository, Depends(get_file_repository)]
PatientRepositoryDep = Annotated[PatientRepository, Depends(get_patient_repository)]
FileStorageDep = Annotated[LocalFileStorageService, Depends(get_file_storage_service)]
NotificationClientDep = Annotated[NotificationClient, Depends(get_notification_client)]


def get_patient_service(
    session: SessionDep,
    patient_repository: PatientRepositoryDep,
    file_repository: FileRepositoryDep,
    file_storage: FileStorageDep,
) -> PatientService:
    return PatientService(
        session=session,
        patient_repository=patient_repository,
        file_repository=file_repository,
        file_storage=file_storage,
    )


PatientServiceDep = Annotated[PatientService, Depends(get_patient_service)]
