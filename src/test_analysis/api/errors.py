"""Mapping of domain errors onto HTTP responses in the `{"error", "detail"}` format."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from test_analysis.extraction import (
    ExtractionFailed,
    ExtractionInvalidResponse,
    FileTooLarge,
    TooManyPages,
    UnsupportedMediaType,
)
from test_analysis.patient_card import (
    DraftNotFoundError,
    DraftStatusConflictError,
    InvalidConfirmRowsError,
    PatientNotFoundError,
    UnknownTestCodeError,
)

# exception class → (HTTP status, API error code)
_STATUS_BY_ERROR: dict[type[Exception], tuple[int, str]] = {
    UnsupportedMediaType: (415, "unsupported_media_type"),
    FileTooLarge: (413, "file_too_large"),
    TooManyPages: (422, "too_many_pages"),
    ExtractionFailed: (502, "extraction_failed"),
    ExtractionInvalidResponse: (502, "extraction_invalid_response"),
    PatientNotFoundError: (404, "patient_not_found"),
    DraftNotFoundError: (404, "draft_not_found"),
    UnknownTestCodeError: (404, "unknown_test_code"),
    DraftStatusConflictError: (409, "draft_status_conflict"),
}


def error_response(status_code: int, error: str, detail: str, **extra: object) -> JSONResponse:
    """Build an API error in the common `{"error", "detail"}` format."""
    return JSONResponse(
        status_code=status_code, content={"error": error, "detail": detail, **extra}
    )


async def handle_domain_error(request: Request, exc: Exception) -> JSONResponse:
    status_code, error = _STATUS_BY_ERROR[type(exc)]
    return error_response(status_code, error, str(exc))


async def handle_invalid_confirm_rows(
    request: Request, exc: InvalidConfirmRowsError
) -> JSONResponse:
    return error_response(422, "invalid_confirm_rows", str(exc), row_ids=exc.row_ids)


async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    error = "not_found" if exc.status_code == 404 else f"http_{exc.status_code}"
    return error_response(exc.status_code, error, str(exc.detail))


async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    return error_response(422, "validation_error", str(exc.errors()))


def register_error_handlers(application: FastAPI) -> None:
    """Attach handlers so that domain errors never surface as 500."""
    for error_class in _STATUS_BY_ERROR:
        application.add_exception_handler(error_class, handle_domain_error)
    application.add_exception_handler(InvalidConfirmRowsError, handle_invalid_confirm_rows)
    application.add_exception_handler(StarletteHTTPException, handle_http_error)
    application.add_exception_handler(RequestValidationError, handle_validation_error)
