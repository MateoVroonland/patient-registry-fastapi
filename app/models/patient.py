from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.file_upload import FileUpload


class Patient(BaseModel):
    __tablename__ = "patients"
    __table_args__ = (UniqueConstraint("email", name="uq_patients_email"),)

    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    phone_number: Mapped[str] = mapped_column(String(30), nullable=False)
    document_file_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("files.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )

    document_file: Mapped[FileUpload] = relationship(
        "FileUpload",
        back_populates="patient",
        lazy="joined",
    )
