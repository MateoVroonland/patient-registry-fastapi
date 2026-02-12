from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile, status

from app.core.constants import MAX_DOCUMENT_PHOTO_SIZE_BYTES, PATIENT_CONFIRMATION_EMAIL_SUBJECT
from app.dependencies import EmailClientDep, PatientServiceDep
from app.schemas.patient import PatientCreateRequest, PatientResponse

router = APIRouter(prefix="/patients", tags=["patients"])

PatientCreateFormDep = Annotated[PatientCreateRequest, Depends(PatientCreateRequest.as_form)]
DocumentPhotoDep = Annotated[
    UploadFile,
    File(
        ...,
        description=(f"Patient document photo (PNG/JPG/JPEG). Max {MAX_DOCUMENT_PHOTO_SIZE_BYTES // (1024 * 1024)}MB."),
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
    email_client: EmailClientDep,
    background_tasks: BackgroundTasks,
) -> PatientResponse:
    patient = await patient_service.create_patient(payload=payload, document_photo=document_photo)
    background_tasks.add_task(
        email_client.send_email,
        to_email=patient.email,
        to_name=patient.full_name,
        subject=PATIENT_CONFIRMATION_EMAIL_SUBJECT,
        body=f"Hello {patient.full_name}, your patient registration was successful.",
    )
    return PatientResponse.model_validate(patient)
