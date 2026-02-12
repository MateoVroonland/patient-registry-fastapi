MAX_DOCUMENT_PHOTO_SIZE_BYTES = 5 * 1024 * 1024

ALLOWED_DOCUMENT_PHOTO_CONTENT_TYPES = frozenset(
    {
        "image/jpeg",
        "image/png",
    },
)

DOCUMENT_PHOTO_CONTENT_TYPE_BY_EXTENSION = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}

ALLOWED_DOCUMENT_PHOTO_EXTENSIONS = frozenset(
    {
        ".jpg",
        ".jpeg",
        ".png",
    },
)
