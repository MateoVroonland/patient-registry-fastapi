from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient

if TYPE_CHECKING:
    from app.schemas.patient import PatientCreateRequest, PatientPatchRequest, PatientPutRequest


class PatientRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, patient_id: UUID) -> Patient | None:
        stmt = select(Patient).where(Patient.id == patient_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_paginated(self, *, offset: int, limit: int) -> list[Patient]:
        stmt = (
            select(Patient)
            .order_by(Patient.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_all(self) -> int:
        stmt = select(func.count()).select_from(Patient)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def get_by_email(self, email: str) -> Patient | None:
        stmt = select(Patient).where(Patient.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email_excluding_id(self, email: str, patient_id: UUID) -> Patient | None:
        stmt = select(Patient).where(
            Patient.email == email,
            Patient.id != patient_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, payload: PatientCreateRequest, document_file_id: UUID) -> Patient:
        patient = Patient(
            id=uuid4(),
            full_name=payload.full_name,
            email=str(payload.email),
            phone_number=payload.phone_number,
            document_file_id=document_file_id,
        )
        self._session.add(patient)
        return patient

    async def replace(
        self,
        patient: Patient,
        payload: PatientPutRequest,
        *,
        document_file_id: UUID | None = None,
    ) -> Patient:
        patient.full_name = payload.full_name
        patient.email = str(payload.email)
        patient.phone_number = payload.phone_number
        if document_file_id is not None:
            patient.document_file_id = document_file_id
        return patient

    async def patch(
        self,
        patient: Patient,
        payload: PatientPatchRequest,
        *,
        document_file_id: UUID | None = None,
    ) -> Patient:
        if payload.full_name is not None:
            patient.full_name = payload.full_name
        if payload.email is not None:
            patient.email = str(payload.email)
        if payload.phone_number is not None:
            patient.phone_number = payload.phone_number
        if document_file_id is not None:
            patient.document_file_id = document_file_id
        return patient

    async def delete(self, patient: Patient) -> None:
        await self._session.delete(patient)
