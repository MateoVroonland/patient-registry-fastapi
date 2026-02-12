from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.patient import Patient


class FileUpload(BaseModel):
    __tablename__ = "files"
    __table_args__ = (CheckConstraint("size_bytes >= 0", name="ck_files_size_nonnegative"),)

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)

    patient: Mapped[Patient | None] = relationship(
        back_populates="document_file",
        uselist=False,
    )
