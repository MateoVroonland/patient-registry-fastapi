from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import (
    ALLOWED_DOCUMENT_PHOTO_CONTENT_TYPES,
    ALLOWED_DOCUMENT_PHOTO_EXTENSIONS,
    DOCUMENT_PHOTO_CONTENT_TYPE_BY_EXTENSION,
)
from app.core.exceptions import DuplicateResourceException, InvalidPayloadException, NotFoundException

if TYPE_CHECKING:
    from app.models.patient import Patient
    from app.repositories.file_repository import FileRepository
    from app.repositories.patient_repository import PatientRepository
    from app.schemas.file_upload import FileUploadCreate
    from app.schemas.patient import PatientCreateRequest, PatientPatchRequest, PatientPutRequest
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

    async def _refresh_patient(self, patient: Patient) -> None:
        await self._session.refresh(
            patient,
            attribute_names=[
                "full_name",
                "email",
                "phone_number",
                "document_file_id",
                "document_file",
                "created_at",
                "updated_at",
            ],
        )

    def _get_document_photo_content_type(self, document_photo: UploadFile) -> str:
        content_type = (document_photo.content_type or "").lower()
        extension = Path(document_photo.filename or "").suffix.lower()
        expected_content_type = DOCUMENT_PHOTO_CONTENT_TYPE_BY_EXTENSION.get(extension)

        if extension not in ALLOWED_DOCUMENT_PHOTO_EXTENSIONS or expected_content_type is None:
            raise InvalidPayloadException("Document photo must be PNG or JPG/JPEG.")

        if content_type not in ALLOWED_DOCUMENT_PHOTO_CONTENT_TYPES or content_type != expected_content_type:
            raise InvalidPayloadException("Document photo must be PNG or JPG/JPEG.")

        return expected_content_type

    async def _save_validated_document_photo(self, document_photo: UploadFile) -> FileUploadCreate:
        expected_content_type = self._get_document_photo_content_type(document_photo=document_photo)
        return await self._file_storage.save_upload(
            upload_file=document_photo,
            content_type=expected_content_type,
        )

    async def get_patient_by_id(self, patient_id: UUID) -> Patient:
        patient = await self._patient_repository.get_by_id(patient_id=patient_id)
        if patient is None:
            raise NotFoundException("Patient was not found.")
        return patient

    async def list_patients(self, *, page: int, size: int) -> tuple[list[Patient], int]:
        offset = (page - 1) * size
        patients = await self._patient_repository.list_paginated(offset=offset, limit=size)
        total = await self._patient_repository.count_all()
        return patients, total

    async def create_patient(self, payload: PatientCreateRequest, document_photo: UploadFile) -> Patient:
        existing_patient = await self._patient_repository.get_by_email(str(payload.email))
        if existing_patient is not None:
            raise DuplicateResourceException("A patient with this email already exists.")

        file_payload = await self._save_validated_document_photo(document_photo=document_photo)

        try:
            file_upload = await self._file_repository.create(file_payload)
            patient = await self._patient_repository.create(
                payload=payload,
                document_file_id=file_upload.id,
            )
            await self._session.commit()
            await self._refresh_patient(patient)
        except Exception:
            await self._session.rollback()
            self._file_storage.delete_file(file_payload.storage_path)
            raise
        else:
            return patient

    async def replace_patient(
        self,
        patient_id: UUID,
        payload: PatientPutRequest,
        *,
        document_photo: UploadFile | None = None,
    ) -> Patient:
        patient = await self.get_patient_by_id(patient_id=patient_id)
        existing_patient = await self._patient_repository.get_by_email_excluding_id(
            email=str(payload.email),
            patient_id=patient_id,
        )
        if existing_patient is not None:
            raise DuplicateResourceException("A patient with this email already exists.")

        new_file_payload: FileUploadCreate | None = None
        old_storage_path: str | None = None

        try:
            if document_photo is not None:
                new_file_payload = await self._save_validated_document_photo(document_photo=document_photo)
                new_file = await self._file_repository.create(new_file_payload)
                old_storage_path = patient.document_file.storage_path
                old_file_id = patient.document_file_id
                await self._patient_repository.replace(
                    patient=patient,
                    payload=payload,
                    document_file_id=new_file.id,
                )
                await self._session.flush()
                await self._file_repository.delete(old_file_id)
            else:
                await self._patient_repository.replace(patient=patient, payload=payload)

            await self._session.commit()
            await self._refresh_patient(patient)
        except Exception:
            await self._session.rollback()
            if new_file_payload is not None:
                self._file_storage.delete_file(new_file_payload.storage_path)
            raise
        else:
            if old_storage_path is not None:
                self._file_storage.delete_file(old_storage_path)
            return patient

    async def patch_patient(
        self,
        patient_id: UUID,
        payload: PatientPatchRequest,
        *,
        document_photo: UploadFile | None = None,
    ) -> Patient:
        if not payload.has_updates() and document_photo is None:
            raise InvalidPayloadException("At least one field or document photo must be provided.")

        patient = await self.get_patient_by_id(patient_id=patient_id)

        if payload.email is not None:
            existing_patient = await self._patient_repository.get_by_email_excluding_id(
                email=str(payload.email),
                patient_id=patient_id,
            )
            if existing_patient is not None:
                raise DuplicateResourceException("A patient with this email already exists.")

        new_file_payload: FileUploadCreate | None = None
        old_storage_path: str | None = None

        try:
            if document_photo is not None:
                new_file_payload = await self._save_validated_document_photo(document_photo=document_photo)
                new_file = await self._file_repository.create(new_file_payload)
                old_storage_path = patient.document_file.storage_path
                old_file_id = patient.document_file_id
                await self._patient_repository.patch(
                    patient=patient,
                    payload=payload,
                    document_file_id=new_file.id,
                )
                await self._session.flush()
                await self._file_repository.delete(old_file_id)
            else:
                await self._patient_repository.patch(patient=patient, payload=payload)

            await self._session.commit()
            await self._refresh_patient(patient)
        except Exception:
            await self._session.rollback()
            if new_file_payload is not None:
                self._file_storage.delete_file(new_file_payload.storage_path)
            raise
        else:
            if old_storage_path is not None:
                self._file_storage.delete_file(old_storage_path)
            return patient

    async def delete_patient(self, patient_id: UUID) -> None:
        patient = await self.get_patient_by_id(patient_id=patient_id)

        document_file_id = patient.document_file_id
        document_storage_path = patient.document_file.storage_path

        try:
            await self._patient_repository.delete(patient)
            await self._session.flush()
            await self._file_repository.delete(document_file_id)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
        else:
            self._file_storage.delete_file(document_storage_path)
