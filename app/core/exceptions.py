from __future__ import annotations

from typing import Any


class AppException(Exception):  # noqa: N818
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


class BadRequestException(AppException):
    def __init__(
        self,
        message: str = "Bad request",
        error_code: str = "BAD_REQUEST",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, status_code=400, error_code=error_code, details=details)


class UnauthorizedException(AppException):
    def __init__(
        self,
        message: str = "Unauthorized",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, status_code=401, error_code="UNAUTHORIZED", details=details)


class ForbiddenException(AppException):
    def __init__(
        self,
        message: str = "Forbidden",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, status_code=403, error_code="FORBIDDEN", details=details)


class NotFoundException(AppException):
    def __init__(
        self,
        message: str = "Resource not found",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, status_code=404, error_code="NOT_FOUND", details=details)


class ConflictException(AppException):
    def __init__(
        self,
        message: str = "Conflict",
        error_code: str = "CONFLICT",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, status_code=409, error_code=error_code, details=details)


class InvalidPayloadException(BadRequestException):
    def __init__(
        self,
        message: str = "Invalid payload",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, error_code="INVALID_PAYLOAD", details=details)


class DuplicateResourceException(ConflictException):
    def __init__(
        self,
        message: str = "Resource already exists",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, error_code="DUPLICATE_RESOURCE", details=details)
