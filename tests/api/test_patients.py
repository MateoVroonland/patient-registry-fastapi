import pytest
from app.core.constants import MAX_DOCUMENT_PHOTO_SIZE_BYTES
from app.core.settings import settings


@pytest.mark.asyncio
async def test_create_patient_returns_created(api_client):
    response = await api_client.post(
        "/patients",
        data={
            "full_name": "Juan Perez",
            "email": "juan.perez@example.com",
            "phone_number": "+5491133344455",
        },
        files={
            "document_photo": ("dni.jpg", b"fake-image-bytes", "image/jpeg"),
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["full_name"] == "Juan Perez"
    assert data["email"] == "juan.perez@example.com"
    assert data["phone_number"] == "+5491133344455"
    assert data["document_file"]["original_filename"] == "dni.jpg"
    assert data["document_file"]["content_type"] == "image/jpeg"
    assert data["document_file"]["size_bytes"] == len(b"fake-image-bytes")
    assert "owner_entity" not in data["document_file"]
    assert "owner_id" not in data["document_file"]

    uploaded_file = settings.uploads_dir / data["document_file"]["storage_path"]
    assert uploaded_file.exists()
    assert uploaded_file.read_bytes() == b"fake-image-bytes"


@pytest.mark.asyncio
async def test_create_patient_accepts_png_document(api_client):
    response = await api_client.post(
        "/patients",
        data={
            "full_name": "Maria Gomez",
            "email": "maria.gomez@example.com",
            "phone_number": "+5491166677788",
        },
        files={
            "document_photo": ("dni.png", b"png-image-bytes", "image/png"),
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["document_file"]["content_type"] == "image/png"
    assert data["document_file"]["original_filename"] == "dni.png"


@pytest.mark.asyncio
async def test_create_patient_returns_422_for_invalid_email(api_client):
    response = await api_client.post(
        "/patients",
        data={
            "full_name": "Juan Perez",
            "email": "not-an-email",
            "phone_number": "+5491133344455",
        },
        files={
            "document_photo": ("dni.jpg", b"fake-image-bytes", "image/jpeg"),
        },
    )

    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "error"
    assert data["code"] == "VALIDATION_ERROR"
    assert data["message"] == "Validation error"
    assert "errors" in data["details"]


@pytest.mark.asyncio
async def test_create_patient_returns_422_for_invalid_phone_number(api_client):
    response = await api_client.post(
        "/patients",
        data={
            "full_name": "Juan Perez",
            "email": "juan.perez@example.com",
            "phone_number": "11-2233-4455",
        },
        files={
            "document_photo": ("dni.jpg", b"fake-image-bytes", "image/jpeg"),
        },
    )

    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "error"
    assert data["code"] == "VALIDATION_ERROR"
    assert data["message"] == "Validation error"
    assert "errors" in data["details"]


@pytest.mark.asyncio
async def test_create_patient_returns_400_for_non_image_document(api_client):
    response = await api_client.post(
        "/patients",
        data={
            "full_name": "Juan Perez",
            "email": "juan.perez@example.com",
            "phone_number": "+5491133344455",
        },
        files={
            "document_photo": ("dni.txt", b"not-an-image", "text/plain"),
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"
    assert data["code"] == "INVALID_PAYLOAD"
    assert data["message"] == "Document photo must be PNG or JPG/JPEG."


@pytest.mark.asyncio
async def test_create_patient_returns_400_for_unsupported_extension(api_client):
    response = await api_client.post(
        "/patients",
        data={
            "full_name": "Juan Perez",
            "email": "juan.perez@example.com",
            "phone_number": "+5491133344455",
        },
        files={
            "document_photo": ("dni.gif", b"fake-image-bytes", "image/jpeg"),
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"
    assert data["code"] == "INVALID_PAYLOAD"
    assert data["message"] == "Document photo must be PNG or JPG/JPEG."


@pytest.mark.asyncio
async def test_create_patient_returns_400_for_file_too_large(api_client):
    too_large_file = b"a" * (MAX_DOCUMENT_PHOTO_SIZE_BYTES + 1)
    response = await api_client.post(
        "/patients",
        data={
            "full_name": "Juan Perez",
            "email": "juan.perez@example.com",
            "phone_number": "+5491133344455",
        },
        files={
            "document_photo": ("dni.jpg", too_large_file, "image/jpeg"),
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"
    assert data["code"] == "INVALID_PAYLOAD"
    assert data["message"] == "Document photo exceeds max size of 5MB."


@pytest.mark.asyncio
async def test_create_patient_returns_409_for_duplicate_email(api_client):
    payload = {
        "full_name": "Juan Perez",
        "email": "juan.perez@example.com",
        "phone_number": "+5491133344455",
    }
    files = {
        "document_photo": ("dni.jpg", b"fake-image-bytes", "image/jpeg"),
    }

    first_response = await api_client.post("/patients", data=payload, files=files)
    assert first_response.status_code == 201

    second_response = await api_client.post(
        "/patients",
        data={
            **payload,
            "full_name": "Juan Segundo",
        },
        files={
            "document_photo": ("dni2.jpg", b"more-image-bytes", "image/jpeg"),
        },
    )
    assert second_response.status_code == 409
    data = second_response.json()
    assert data["status"] == "error"
    assert data["code"] == "DUPLICATE_RESOURCE"
    assert data["message"] == "A patient with this email already exists."


@pytest.mark.asyncio
async def test_openapi_includes_patient_creation_docs(api_client):
    response = await api_client.get("/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    post_operation = schema["paths"]["/patients"]["post"]
    assert post_operation["summary"] == "Create patient"
    assert "multipart/form-data" in post_operation["requestBody"]["content"]
