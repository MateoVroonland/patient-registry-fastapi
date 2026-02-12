from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.constants import MAX_DOCUMENT_PHOTO_SIZE_BYTES
from app.dependencies import PatientServiceDep
from app.schemas.patient import PatientCreateRequest, PatientResponse
from app.services.errors import DuplicateResourceError, InvalidPayloadError

router = APIRouter(prefix="/patients", tags=["patients"])

PatientCreateFormDep = Annotated[PatientCreateRequest, Depends(PatientCreateRequest.as_form)]
DocumentPhotoDep = Annotated[
    UploadFile,
    File(
        ...,
        description=(
            f"Patient document photo (PNG/JPG/JPEG). Max "
            f"{MAX_DOCUMENT_PHOTO_SIZE_BYTES // (1024 * 1024)}MB."
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
) -> PatientResponse:
    try:
        patient = await patient_service.create_patient(payload=payload, document_photo=document_photo)
    except DuplicateResourceError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except InvalidPayloadError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return PatientResponse.model_validate(patient)
