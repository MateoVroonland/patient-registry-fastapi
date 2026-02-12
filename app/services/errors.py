class ServiceError(Exception):
    """Base class for service-layer exceptions."""


class DuplicateResourceError(ServiceError):
    """Raised when trying to create a resource that already exists."""


class InvalidPayloadError(ServiceError):
    """Raised when the input payload is invalid for business rules."""


class ResourceNotFoundError(ServiceError):
    """Raised when a requested resource does not exist."""
