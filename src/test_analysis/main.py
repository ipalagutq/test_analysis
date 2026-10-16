"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from test_analysis import __version__
from test_analysis.api import api_router
from test_analysis.config import get_settings
from test_analysis.patient_card import create_schema, get_session_factory
from test_analysis.seed import seed_if_empty


def error_response(status_code: int, error: str, detail: str) -> JSONResponse:
    """Build an API error in the common `{"error", "detail"}` format."""
    return JSONResponse(status_code=status_code, content={"error": error, "detail": detail})


async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    error = "not_found" if exc.status_code == 404 else f"http_{exc.status_code}"
    return error_response(exc.status_code, error, str(exc.detail))


async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    return error_response(422, "validation_error", str(exc.errors()))


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Create the patient card schema and seed demo patients into an empty database."""
    create_schema()
    with get_session_factory()() as session:
        seed_if_empty(session)
    yield


def create_app() -> FastAPI:
    """Build the application; fails fast on invalid configuration."""
    get_settings()
    application = FastAPI(title="Lab Scan Reader", version=__version__, lifespan=lifespan)
    application.add_exception_handler(StarletteHTTPException, handle_http_error)
    application.add_exception_handler(RequestValidationError, handle_validation_error)
    application.include_router(api_router)
    return application


app = create_app()
