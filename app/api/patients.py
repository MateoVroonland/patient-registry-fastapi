from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, UploadFile, status

from app.core.constants import MAX_DOCUMENT_PHOTO_SIZE_BYTES, PATIENT_CONFIRMATION_EMAIL_SUBJECT
from app.dependencies import NotificationClientDep, PatientServiceDep
from app.schemas.patient import (
    PatientCreateRequest,
    PatientListResponse,
    PatientPatchRequest,
    PatientPutRequest,
    PatientResponse,
)
from app.services.notification_client import NotificationMessage

router = APIRouter(prefix="/patients", tags=["patients"])

PatientCreateFormDep = Annotated[PatientCreateRequest, Depends(PatientCreateRequest.as_form)]
PatientPutFormDep = Annotated[PatientPutRequest, Depends(PatientPutRequest.as_form)]
PatientPatchFormDep = Annotated[PatientPatchRequest, Depends(PatientPatchRequest.as_form)]
DocumentPhotoDep = Annotated[
    UploadFile,
    File(
        ...,
        description=(f"Patient document photo (PNG/JPG/JPEG). Max {MAX_DOCUMENT_PHOTO_SIZE_BYTES // (1024 * 1024)}MB."),
    ),
]
OptionalDocumentPhotoDep = Annotated[
    UploadFile | None,
    File(
        description=(
            f"Optional patient document photo (PNG/JPG/JPEG). Max {MAX_DOCUMENT_PHOTO_SIZE_BYTES // (1024 * 1024)}MB."
        ),
    ),
]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create patient",
    description="Registers a patient and stores the document photo in local storage.",
    responses={
        status.HTTP_201_CREATED: {"description": "Patient created successfully."},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid payload."},
        status.HTTP_409_CONFLICT: {"description": "Patient already exists."},
    },
)
async def create_patient(
    payload: PatientCreateFormDep,
    document_photo: DocumentPhotoDep,
    patient_service: PatientServiceDep,
    notification_client: NotificationClientDep,
    background_tasks: BackgroundTasks,
) -> PatientResponse:
    patient = await patient_service.create_patient(payload=payload, document_photo=document_photo)
    notification_message = NotificationMessage(
        recipient=patient.email,
        recipient_name=patient.full_name,
        subject=PATIENT_CONFIRMATION_EMAIL_SUBJECT,
        body=f"Hello {patient.full_name}, your patient registration was successful.",
    )
    background_tasks.add_task(
        notification_client.send_notification,
        message=notification_message,
    )
    return PatientResponse.model_validate(patient)


@router.get(
    "",
    summary="List patients",
    description="Returns a paginated list of patients.",
)
async def list_patients(
    patient_service: PatientServiceDep,
    page: Annotated[int, Query(ge=1, description="Page number.")] = 1,
    size: Annotated[int, Query(ge=1, le=100, description="Page size.")] = 20,
) -> PatientListResponse:
    patients, total = await patient_service.list_patients(page=page, size=size)
    return PatientListResponse(
        items=[PatientResponse.model_validate(patient) for patient in patients],
        page=page,
        size=size,
        total=total,
    )


@router.get(
    "/{patient_id}",
    summary="Get patient by ID",
    responses={
        status.HTTP_200_OK: {"description": "Patient retrieved successfully."},
        status.HTTP_404_NOT_FOUND: {"description": "Patient not found."},
    },
)
async def get_patient_by_id(
    patient_id: UUID,
    patient_service: PatientServiceDep,
) -> PatientResponse:
    patient = await patient_service.get_patient_by_id(patient_id=patient_id)
    return PatientResponse.model_validate(patient)


@router.put(
    "/{patient_id}",
    summary="Replace patient",
    description="Replaces all mutable patient fields and optionally replaces document photo.",
    responses={
        status.HTTP_200_OK: {"description": "Patient replaced successfully."},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid payload."},
        status.HTTP_404_NOT_FOUND: {"description": "Patient not found."},
        status.HTTP_409_CONFLICT: {"description": "Patient already exists."},
    },
)
async def replace_patient(
    patient_id: UUID,
    payload: PatientPutFormDep,
    patient_service: PatientServiceDep,
    document_photo: OptionalDocumentPhotoDep = None,
) -> PatientResponse:
    patient = await patient_service.replace_patient(
        patient_id=patient_id,
        payload=payload,
        document_photo=document_photo,
    )
    return PatientResponse.model_validate(patient)


@router.patch(
    "/{patient_id}",
    summary="Patch patient",
    description="Updates any subset of patient fields and optionally replaces document photo.",
    responses={
        status.HTTP_200_OK: {"description": "Patient patched successfully."},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid payload."},
        status.HTTP_404_NOT_FOUND: {"description": "Patient not found."},
    },
)
async def patch_patient(
    patient_id: UUID,
    payload: PatientPatchFormDep,
    patient_service: PatientServiceDep,
    document_photo: OptionalDocumentPhotoDep = None,
) -> PatientResponse:
    patient = await patient_service.patch_patient(
        patient_id=patient_id,
        payload=payload,
        document_photo=document_photo,
    )
    return PatientResponse.model_validate(patient)


@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete patient",
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Patient deleted successfully."},
        status.HTTP_404_NOT_FOUND: {"description": "Patient not found."},
    },
)
async def delete_patient(
    patient_id: UUID,
    patient_service: PatientServiceDep,
) -> None:
    await patient_service.delete_patient(patient_id=patient_id)
