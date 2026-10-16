"""FastAPI application entry point."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from test_analysis import __version__
from test_analysis.api import api_router
from test_analysis.config import get_settings


def error_response(status_code: int, error: str, detail: str) -> JSONResponse:
    """Build an API error in the common `{"error", "detail"}` format."""
    return JSONResponse(status_code=status_code, content={"error": error, "detail": detail})


async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    error = "not_found" if exc.status_code == 404 else f"http_{exc.status_code}"
    return error_response(exc.status_code, error, str(exc.detail))


async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    return error_response(422, "validation_error", str(exc.errors()))


def create_app() -> FastAPI:
    """Build the application; fails fast on invalid configuration."""
    get_settings()
    application = FastAPI(title="Lab Scan Reader", version=__version__)
    application.add_exception_handler(StarletteHTTPException, handle_http_error)
    application.add_exception_handler(RequestValidationError, handle_validation_error)
    application.include_router(api_router)
    return application


app = create_app()
