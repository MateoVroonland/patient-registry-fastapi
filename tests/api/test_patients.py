from uuid import uuid4

import pytest

from app.core.constants import MAX_DOCUMENT_PHOTO_SIZE_BYTES, PATIENT_CONFIRMATION_EMAIL_SUBJECT
from app.core.settings import settings
from app.dependencies import get_notification_client
from app.main import app
from app.services.notification_client import NoopNotificationClient, NotificationMessage

DEFAULT_PATIENT_PAYLOAD = {
    "full_name": "Juan Perez",
    "email": "juan.perez@example.com",
    "phone_number": "+5491133344455",
}

DEFAULT_DOCUMENT_PHOTO = ("dni.jpg", b"fake-image-bytes", "image/jpeg")
PNG_DOCUMENT_PHOTO = ("dni.png", b"png-image-bytes", "image/png")
NON_IMAGE_DOCUMENT_PHOTO = ("dni.txt", b"not-an-image", "text/plain")


def build_payload(**overrides: str) -> dict[str, str]:
    return {**DEFAULT_PATIENT_PAYLOAD, **overrides}


def build_document_photo(
    filename: str,
    content: bytes,
    content_type: str,
) -> dict[str, tuple[str, bytes, str]]:
    return {"document_photo": (filename, content, content_type)}


async def post_patient(
    api_client,
    payload: dict[str, str] | None = None,
    document_photo: tuple[str, bytes, str] = DEFAULT_DOCUMENT_PHOTO,
):
    request_payload = payload or build_payload()
    return await api_client.post(
        "/patients",
        data=request_payload,
        files=build_document_photo(*document_photo),
    )


async def create_patient_and_get_body(
    api_client,
    payload: dict[str, str] | None = None,
    document_photo: tuple[str, bytes, str] = DEFAULT_DOCUMENT_PHOTO,
) -> dict:
    response = await post_patient(
        api_client,
        payload=payload,
        document_photo=document_photo,
    )
    assert response.status_code == 201
    return response.json()


def assert_error_response(response, *, status_code: int, code: str, message: str) -> None:
    assert response.status_code == status_code
    data = response.json()
    assert data["status"] == "error"
    assert data["code"] == code
    assert data["message"] == message


class EmailServiceSpy:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    async def send_notification(self, *, message: NotificationMessage) -> None:
        self.calls.append(
            {
                "recipient": message.recipient,
                "recipient_name": message.recipient_name or "",
                "subject": message.subject or "",
                "body": message.body,
            },
        )


class SpyNoopNotificationClient(NoopNotificationClient):
    def __init__(self) -> None:
        self.spy = EmailServiceSpy()

    async def send_notification(self, *, message: NotificationMessage) -> None:
        await self.spy.send_notification(message=message)
        await super().send_notification(message=message)


@pytest.mark.asyncio
async def test_create_patient_returns_created(api_client):
    response = await post_patient(api_client)

    assert response.status_code == 201
    data = response.json()
    assert data["full_name"] == DEFAULT_PATIENT_PAYLOAD["full_name"]
    assert data["email"] == DEFAULT_PATIENT_PAYLOAD["email"]
    assert data["phone_number"] == DEFAULT_PATIENT_PAYLOAD["phone_number"]
    assert data["document_file"]["original_filename"] == DEFAULT_DOCUMENT_PHOTO[0]
    assert data["document_file"]["content_type"] == DEFAULT_DOCUMENT_PHOTO[2]
    assert data["document_file"]["size_bytes"] == len(DEFAULT_DOCUMENT_PHOTO[1])
    assert "owner_entity" not in data["document_file"]
    assert "owner_id" not in data["document_file"]

    uploaded_file = settings.uploads_dir / data["document_file"]["storage_path"]
    assert uploaded_file.exists()
    assert uploaded_file.read_bytes() == DEFAULT_DOCUMENT_PHOTO[1]


@pytest.mark.asyncio
async def test_get_patient_by_id_returns_patient(api_client):
    created = await create_patient_and_get_body(api_client)

    response = await api_client.get(f"/patients/{created['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]
    assert data["email"] == created["email"]


@pytest.mark.asyncio
async def test_get_patient_by_id_returns_404_when_missing(api_client):
    response = await api_client.get(f"/patients/{uuid4()}")
    assert_error_response(
        response,
        status_code=404,
        code="NOT_FOUND",
        message="Patient was not found.",
    )


@pytest.mark.asyncio
async def test_list_patients_returns_paginated_results(api_client):
    await create_patient_and_get_body(api_client, payload=build_payload(email="first@example.com"))
    await create_patient_and_get_body(api_client, payload=build_payload(email="second@example.com"))
    await create_patient_and_get_body(api_client, payload=build_payload(email="third@example.com"))

    first_page_response = await api_client.get("/patients?page=1&size=2")
    assert first_page_response.status_code == 200
    first_page = first_page_response.json()
    assert first_page["page"] == 1
    assert first_page["size"] == 2
    assert first_page["total"] == 3
    assert len(first_page["items"]) == 2

    second_page_response = await api_client.get("/patients?page=2&size=2")
    assert second_page_response.status_code == 200
    second_page = second_page_response.json()
    assert second_page["page"] == 2
    assert second_page["size"] == 2
    assert second_page["total"] == 3
    assert len(second_page["items"]) == 1


@pytest.mark.asyncio
async def test_create_patient_sends_confirmation_email(api_client):
    noop_spy = SpyNoopNotificationClient()
    app.dependency_overrides[get_notification_client] = lambda: noop_spy

    try:
        response = await post_patient(api_client)
        assert response.status_code == 201
        assert len(noop_spy.spy.calls) == 1
        call = noop_spy.spy.calls[0]
        assert call["recipient"] == DEFAULT_PATIENT_PAYLOAD["email"]
        assert call["recipient_name"] == DEFAULT_PATIENT_PAYLOAD["full_name"]
        assert call["subject"] == PATIENT_CONFIRMATION_EMAIL_SUBJECT
        assert "successful" in call["body"]
    finally:
        app.dependency_overrides.pop(get_notification_client, None)


@pytest.mark.asyncio
async def test_create_patient_accepts_png_document(api_client):
    response = await post_patient(
        api_client,
        payload=build_payload(
            full_name="Maria Gomez",
            email="maria.gomez@example.com",
            phone_number="+5491166677788",
        ),
        document_photo=PNG_DOCUMENT_PHOTO,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["document_file"]["content_type"] == PNG_DOCUMENT_PHOTO[2]
    assert data["document_file"]["original_filename"] == PNG_DOCUMENT_PHOTO[0]


@pytest.mark.asyncio
async def test_create_patient_returns_422_for_invalid_email(api_client):
    response = await post_patient(
        api_client,
        payload=build_payload(email="not-an-email"),
    )

    assert_error_response(
        response,
        status_code=422,
        code="VALIDATION_ERROR",
        message="Validation error",
    )
    data = response.json()
    assert "errors" in data["details"]


@pytest.mark.asyncio
async def test_create_patient_returns_422_for_invalid_phone_number(api_client):
    response = await post_patient(
        api_client,
        payload=build_payload(phone_number="11-2233-4455"),
    )

    assert_error_response(
        response,
        status_code=422,
        code="VALIDATION_ERROR",
        message="Validation error",
    )
    data = response.json()
    assert "errors" in data["details"]


@pytest.mark.asyncio
async def test_create_patient_returns_400_for_non_image_document(api_client):
    response = await post_patient(
        api_client,
        document_photo=NON_IMAGE_DOCUMENT_PHOTO,
    )

    assert_error_response(
        response,
        status_code=400,
        code="INVALID_PAYLOAD",
        message="Document photo must be PNG or JPG/JPEG.",
    )


@pytest.mark.asyncio
async def test_create_patient_returns_400_for_unsupported_extension(api_client):
    response = await post_patient(
        api_client,
        document_photo=("dni.gif", b"fake-image-bytes", "image/jpeg"),
    )

    assert_error_response(
        response,
        status_code=400,
        code="INVALID_PAYLOAD",
        message="Document photo must be PNG or JPG/JPEG.",
    )


@pytest.mark.asyncio
async def test_create_patient_returns_400_for_file_too_large(api_client):
    response = await post_patient(
        api_client,
        document_photo=(
            "dni.jpg",
            b"a" * (MAX_DOCUMENT_PHOTO_SIZE_BYTES + 1),
            "image/jpeg",
        ),
    )

    assert_error_response(
        response,
        status_code=400,
        code="INVALID_PAYLOAD",
        message="Document photo exceeds max size of 5MB.",
    )


@pytest.mark.asyncio
async def test_create_patient_returns_409_for_duplicate_email(api_client):
    first_response = await post_patient(api_client)
    assert first_response.status_code == 201

    second_response = await post_patient(
        api_client,
        payload=build_payload(full_name="Juan Segundo"),
        document_photo=("dni2.jpg", b"more-image-bytes", "image/jpeg"),
    )
    assert_error_response(
        second_response,
        status_code=409,
        code="DUPLICATE_RESOURCE",
        message="A patient with this email already exists.",
    )


@pytest.mark.asyncio
async def test_create_patient_does_not_send_extra_confirmation_email_on_duplicate(api_client):
    noop_spy = SpyNoopNotificationClient()
    app.dependency_overrides[get_notification_client] = lambda: noop_spy

    try:
        first_response = await post_patient(api_client)
        assert first_response.status_code == 201

        second_response = await post_patient(
            api_client,
            payload=build_payload(full_name="Juan Segundo"),
            document_photo=("dni2.jpg", b"more-image-bytes", "image/jpeg"),
        )
        assert second_response.status_code == 409
        assert len(noop_spy.spy.calls) == 1
    finally:
        app.dependency_overrides.pop(get_notification_client, None)


@pytest.mark.asyncio
async def test_patch_patient_updates_partial_fields(api_client):
    created = await create_patient_and_get_body(api_client)

    response = await api_client.patch(
        f"/patients/{created['id']}",
        data={"full_name": "Juan Updated"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Juan Updated"
    assert data["email"] == created["email"]


@pytest.mark.asyncio
async def test_patch_patient_replaces_document_photo(api_client):
    created = await create_patient_and_get_body(api_client)
    old_storage_path = created["document_file"]["storage_path"]
    old_file = settings.uploads_dir / old_storage_path
    assert old_file.exists()

    response = await api_client.patch(
        f"/patients/{created['id']}",
        files=build_document_photo("updated.png", b"updated-png-bytes", "image/png"),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["document_file"]["original_filename"] == "updated.png"
    assert data["document_file"]["content_type"] == "image/png"
    assert data["document_file"]["storage_path"] != old_storage_path
    assert not old_file.exists()


@pytest.mark.asyncio
async def test_patch_patient_returns_400_when_empty_payload(api_client):
    created = await create_patient_and_get_body(api_client)

    response = await api_client.patch(f"/patients/{created['id']}")
    assert_error_response(
        response,
        status_code=400,
        code="INVALID_PAYLOAD",
        message="At least one field or document photo must be provided.",
    )


@pytest.mark.asyncio
async def test_patch_patient_returns_409_for_duplicate_email(api_client):
    first = await create_patient_and_get_body(api_client, payload=build_payload(email="first@example.com"))
    await create_patient_and_get_body(api_client, payload=build_payload(email="second@example.com"))

    response = await api_client.patch(
        f"/patients/{first['id']}",
        data={"email": "second@example.com"},
    )
    assert_error_response(
        response,
        status_code=409,
        code="DUPLICATE_RESOURCE",
        message="A patient with this email already exists.",
    )


@pytest.mark.asyncio
async def test_put_patient_replaces_fields_without_replacing_document(api_client):
    created = await create_patient_and_get_body(api_client)
    storage_path = created["document_file"]["storage_path"]

    response = await api_client.put(
        f"/patients/{created['id']}",
        data={
            "full_name": "Juan Replaced",
            "email": "juan.replaced@example.com",
            "phone_number": "+5491133344466",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Juan Replaced"
    assert data["email"] == "juan.replaced@example.com"
    assert data["phone_number"] == "+5491133344466"
    assert data["document_file"]["storage_path"] == storage_path


@pytest.mark.asyncio
async def test_put_patient_replaces_document_photo_when_provided(api_client):
    created = await create_patient_and_get_body(api_client)
    old_storage_path = created["document_file"]["storage_path"]
    old_file = settings.uploads_dir / old_storage_path
    assert old_file.exists()

    response = await api_client.put(
        f"/patients/{created['id']}",
        data={
            "full_name": "Juan Replaced",
            "email": "juan.replaced@example.com",
            "phone_number": "+5491133344466",
        },
        files=build_document_photo("replaced.png", b"replaced-png-bytes", "image/png"),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["document_file"]["original_filename"] == "replaced.png"
    assert data["document_file"]["content_type"] == "image/png"
    assert data["document_file"]["storage_path"] != old_storage_path
    assert not old_file.exists()


@pytest.mark.asyncio
async def test_put_patient_returns_409_for_duplicate_email(api_client):
    first = await create_patient_and_get_body(api_client, payload=build_payload(email="first@example.com"))
    await create_patient_and_get_body(api_client, payload=build_payload(email="second@example.com"))

    response = await api_client.put(
        f"/patients/{first['id']}",
        data={
            "full_name": "Juan Updated",
            "email": "second@example.com",
            "phone_number": "+5491133344466",
        },
    )
    assert_error_response(
        response,
        status_code=409,
        code="DUPLICATE_RESOURCE",
        message="A patient with this email already exists.",
    )


@pytest.mark.asyncio
async def test_delete_patient_removes_patient_and_document_file(api_client):
    created = await create_patient_and_get_body(api_client)
    storage_path = created["document_file"]["storage_path"]
    uploaded_file = settings.uploads_dir / storage_path
    assert uploaded_file.exists()

    delete_response = await api_client.delete(f"/patients/{created['id']}")
    assert delete_response.status_code == 204
    assert not uploaded_file.exists()

    get_response = await api_client.get(f"/patients/{created['id']}")
    assert_error_response(
        get_response,
        status_code=404,
        code="NOT_FOUND",
        message="Patient was not found.",
    )


@pytest.mark.asyncio
async def test_delete_patient_returns_404_when_missing(api_client):
    response = await api_client.delete(f"/patients/{uuid4()}")
    assert_error_response(
        response,
        status_code=404,
        code="NOT_FOUND",
        message="Patient was not found.",
    )
