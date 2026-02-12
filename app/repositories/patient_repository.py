from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient

if TYPE_CHECKING:
    from app.schemas.patient import PatientCreateRequest


class PatientRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> Patient | None:
        stmt = select(Patient).where(Patient.email == email)
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
