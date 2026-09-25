"""
error_handlers.py — graceful failure handling.

Domain errors are translated into precise HTTP status codes instead of
ugly 500s — a professional API contract:

    FileValidationError -> 415 Unsupported Media Type
    DeadlineError       -> 409 Conflict (late submissions blocked)
    StorageError        -> 503 Service Unavailable (storage outage)
    ValueError (grading)-> 400 Bad Request
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from backend.utils.validators import FileSizeError, FileValidationError
from backend.utils.deadline import DeadlineError
from backend.cloud.storage_service import StorageError


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(FileSizeError)
    async def _file_size_handler(_: Request, exc: FileSizeError):
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"detail": str(exc)},
        )

    @app.exception_handler(FileValidationError)
    async def _file_validation_handler(_: Request, exc: FileValidationError):
        return JSONResponse(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            content={"detail": str(exc)},
        )

    @app.exception_handler(DeadlineError)
    async def _deadline_handler(_: Request, exc: DeadlineError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": str(exc),
                "deadline": exc.deadline.isoformat(),
            },
        )

    @app.exception_handler(StorageError)
    async def _storage_handler(_: Request, exc: StorageError):
        # Cloud object storage is temporarily unavailable — client may retry.
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": f"Storage service unavailable: {exc}"},
        )

    @app.exception_handler(ValueError)
    async def _value_error_handler(_: Request, exc: ValueError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )
