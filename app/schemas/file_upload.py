from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FileUploadCreate(BaseModel):
    original_filename: str = Field(min_length=1, max_length=255)
    storage_path: str = Field(min_length=1, max_length=512)
    content_type: str = Field(min_length=1, max_length=255)
    size_bytes: int = Field(ge=0)


class FileUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_filename: str
    storage_path: str
    content_type: str
    size_bytes: int
    created_at: datetime
    updated_at: datetime
