from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.repositories.file_repository import FileRepository
from app.repositories.patient_repository import PatientRepository
from app.services.file_storage_service import LocalFileStorageService
from app.services.patient_service import PatientService

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_file_storage_service() -> LocalFileStorageService:
    return LocalFileStorageService()


def get_file_repository(session: SessionDep) -> FileRepository:
    return FileRepository(session=session)


def get_patient_repository(session: SessionDep) -> PatientRepository:
    return PatientRepository(session=session)


FileRepositoryDep = Annotated[FileRepository, Depends(get_file_repository)]
PatientRepositoryDep = Annotated[PatientRepository, Depends(get_patient_repository)]
FileStorageDep = Annotated[LocalFileStorageService, Depends(get_file_storage_service)]


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
