from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import Form
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ConfigDict, EmailStr, Field, ValidationError


class PatientCreateRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    phone_number: str = Field(min_length=7, max_length=20, pattern=r"^\+?[0-9]{7,20}$")

    @classmethod
    def as_form(
        cls,
        full_name: Annotated[
            str,
            Form(
                ...,
                description="Patient full name.",
                examples=["Juan Perez"],
            ),
        ],
        email: Annotated[
            EmailStr,
            Form(
                ...,
                description="Patient email.",
                examples=["juan.perez@example.com"],
            ),
        ],
        phone_number: Annotated[
            str,
            Form(
                ...,
                description="Patient phone number in international format.",
                examples=["+5491133344455"],
            ),
        ],
    ) -> PatientCreateRequest:
        try:
            return cls(
                full_name=full_name,
                email=email,
                phone_number=phone_number,
            )
        except ValidationError as exc:
            raise RequestValidationError(exc.errors()) from exc


class PatientPutRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    phone_number: str = Field(min_length=7, max_length=20, pattern=r"^\+?[0-9]{7,20}$")

    @classmethod
    def as_form(
        cls,
        full_name: Annotated[
            str,
            Form(
                ...,
                description="Patient full name.",
                examples=["Juan Perez"],
            ),
        ],
        email: Annotated[
            EmailStr,
            Form(
                ...,
                description="Patient email.",
                examples=["juan.perez@example.com"],
            ),
        ],
        phone_number: Annotated[
            str,
            Form(
                ...,
                description="Patient phone number in international format.",
                examples=["+5491133344455"],
            ),
        ],
    ) -> PatientPutRequest:
        try:
            return cls(
                full_name=full_name,
                email=email,
                phone_number=phone_number,
            )
        except ValidationError as exc:
            raise RequestValidationError(exc.errors()) from exc


class PatientPatchRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    email: EmailStr | None = None
    phone_number: str | None = Field(default=None, min_length=7, max_length=20, pattern=r"^\+?[0-9]{7,20}$")

    @classmethod
    def as_form(
        cls,
        full_name: Annotated[
            str | None,
            Form(
                description="Patient full name.",
                examples=["Juan Perez"],
            ),
        ] = None,
        email: Annotated[
            EmailStr | None,
            Form(
                description="Patient email.",
                examples=["juan.perez@example.com"],
            ),
        ] = None,
        phone_number: Annotated[
            str | None,
            Form(
                description="Patient phone number in international format.",
                examples=["+5491133344455"],
            ),
        ] = None,
    ) -> PatientPatchRequest:
        try:
            return cls(
                full_name=full_name,
                email=email,
                phone_number=phone_number,
            )
        except ValidationError as exc:
            raise RequestValidationError(exc.errors()) from exc

    def has_updates(self) -> bool:
        return any(
            (
                self.full_name is not None,
                self.email is not None,
                self.phone_number is not None,
            ),
        )


class PatientDocumentFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_filename: str
    storage_path: str
    content_type: str
    size_bytes: int
    created_at: datetime
    updated_at: datetime


class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    email: EmailStr
    phone_number: str
    document_file: PatientDocumentFileResponse
    created_at: datetime
    updated_at: datetime


class PatientListResponse(BaseModel):
    items: list[PatientResponse]
    page: int = Field(ge=1)
    size: int = Field(ge=1)
    total: int = Field(ge=0)
