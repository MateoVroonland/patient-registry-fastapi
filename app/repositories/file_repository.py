from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file_upload import FileUpload

if TYPE_CHECKING:
    from app.schemas.file_upload import FileUploadCreate


class FileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, payload: FileUploadCreate) -> FileUpload:
        file_upload = FileUpload(id=uuid4(), **payload.model_dump())
        self._session.add(file_upload)
        return file_upload

    async def get_by_id(self, file_id: UUID) -> FileUpload | None:
        stmt = select(FileUpload).where(FileUpload.id == file_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, file_id: UUID) -> None:
        stmt = delete(FileUpload).where(FileUpload.id == file_id)
        await self._session.execute(stmt)
