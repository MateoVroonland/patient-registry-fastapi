from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ALLOWED_DOCUMENT_PHOTO_CONTENT_TYPES, ALLOWED_DOCUMENT_PHOTO_EXTENSIONS
from app.services.errors import DuplicateResourceError, InvalidPayloadError

if TYPE_CHECKING:
    from app.models.patient import Patient
    from app.repositories.file_repository import FileRepository
    from app.repositories.patient_repository import PatientRepository
    from app.schemas.patient import PatientCreateRequest
    from app.services.file_storage_service import LocalFileStorageService


class PatientService:
    def __init__(
        self,
        session: AsyncSession,
        patient_repository: PatientRepository,
        file_repository: FileRepository,
        file_storage: LocalFileStorageService,
    ) -> None:
        self._session = session
        self._patient_repository = patient_repository
        self._file_repository = file_repository
        self._file_storage = file_storage

    async def create_patient(self, payload: PatientCreateRequest, document_photo: UploadFile) -> Patient:
        existing_patient = await self._patient_repository.get_by_email(str(payload.email))
        if existing_patient is not None:
            raise DuplicateResourceError("A patient with this email already exists.")

        content_type = (document_photo.content_type or "").lower()
        extension = Path(document_photo.filename or "").suffix.lower()

        if content_type not in ALLOWED_DOCUMENT_PHOTO_CONTENT_TYPES or extension not in ALLOWED_DOCUMENT_PHOTO_EXTENSIONS:
            raise InvalidPayloadError("Document photo must be PNG or JPG/JPEG.")

        file_payload = await self._file_storage.save_upload(upload_file=document_photo)

        try:
            file_upload = await self._file_repository.create(file_payload)
            patient = await self._patient_repository.create(
                payload=payload,
                document_file_id=file_upload.id,
            )
            await self._session.commit()
            await self._session.refresh(patient, attribute_names=["document_file"])
        except Exception:
            await self._session.rollback()
            self._file_storage.delete_file(file_payload.storage_path)
            raise
        else:
            return patient
