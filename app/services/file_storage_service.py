from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.constants import MAX_DOCUMENT_PHOTO_SIZE_BYTES
from app.core.exceptions import InvalidPayloadException
from app.core.settings import settings
from app.schemas.file_upload import FileUploadCreate


class LocalFileStorageService:
    def __init__(
        self,
        uploads_dir: Path | None = None,
        chunk_size: int | None = None,
        max_file_size_bytes: int = MAX_DOCUMENT_PHOTO_SIZE_BYTES,
    ) -> None:
        self._uploads_dir = uploads_dir or settings.uploads_dir
        self._chunk_size = chunk_size or settings.file_chunk_size
        self._max_file_size_bytes = max_file_size_bytes
        self._uploads_dir.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, upload_file: UploadFile) -> FileUploadCreate:
        server_uid = uuid4()
        suffix = Path(upload_file.filename or "").suffix.lower()
        server_filename = f"{server_uid}{suffix}" if suffix else str(server_uid)
        storage_path = server_filename
        absolute_path = self.resolve_path(storage_path)

        size_bytes = 0
        try:
            with absolute_path.open("wb") as output_file:
                while chunk := await upload_file.read(self._chunk_size):
                    size_bytes += len(chunk)
                    if size_bytes > self._max_file_size_bytes:
                        output_file.close()
                        self.delete_file(storage_path)
                        message = f"Document photo exceeds max size of {self._max_file_size_bytes // (1024 * 1024)}MB."
                        raise InvalidPayloadException(message)
                    output_file.write(chunk)
        finally:
            await upload_file.close()

        return FileUploadCreate(
            server_filename=server_filename,
            original_filename=Path(upload_file.filename or server_filename).name,
            storage_path=storage_path,
            content_type=upload_file.content_type or "application/octet-stream",
            size_bytes=size_bytes,
        )

    def resolve_path(self, storage_path: str) -> Path:
        return self._uploads_dir / storage_path

    def delete_file(self, storage_path: str) -> None:
        absolute_path = self.resolve_path(storage_path)
        if absolute_path.exists():
            absolute_path.unlink()
