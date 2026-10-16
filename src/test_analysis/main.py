"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from test_analysis import __version__
from test_analysis.api import api_router
from test_analysis.api.errors import register_error_handlers
from test_analysis.config import get_settings
from test_analysis.patient_card import create_schema, get_session_factory
from test_analysis.seed import seed_if_empty


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
    register_error_handlers(application)
    application.include_router(api_router)
    return application


app = create_app()
