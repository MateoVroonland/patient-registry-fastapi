from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import AppException
from app.core.logging import get_logger

logger = get_logger(__name__)

INTERNAL_SERVER_ERROR = 500


async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
    status_code: int
    message: str
    error_code: str
    details: dict[str, object]

    if isinstance(exc, AppException):
        status_code = exc.status_code
        message = exc.message
        error_code = exc.error_code
        details = exc.details
    elif isinstance(exc, RequestValidationError):
        status_code = 422
        message = "Validation error"
        error_code = "VALIDATION_ERROR"
        details = {"errors": exc.errors()}
    elif isinstance(exc, HTTPException):
        status_code = exc.status_code
        message = str(exc.detail)
        error_code = "HTTP_ERROR"
        details = {}
    else:
        status_code = INTERNAL_SERVER_ERROR
        message = "Internal server error"
        error_code = "INTERNAL_ERROR"
        details = {}
        logger.error(
            "Unhandled exception: %s %s",
            request.method,
            request.url.path,
            exc_info=exc,
        )

    if status_code >= INTERNAL_SERVER_ERROR:
        logger.error(
            "%s %s -> %s (%s)",
            request.method,
            request.url.path,
            message,
            error_code,
        )
    else:
        logger.warning(
            "%s %s -> %s (%s)",
            request.method,
            request.url.path,
            message,
            error_code,
        )

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "error",
            "code": error_code,
            "message": message,
            "details": details,
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, exception_handler)
    app.add_exception_handler(RequestValidationError, exception_handler)
    app.add_exception_handler(HTTPException, exception_handler)
    app.add_exception_handler(Exception, exception_handler)
