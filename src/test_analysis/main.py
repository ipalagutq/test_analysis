"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
from starlette.types import Scope

from test_analysis import __version__
from test_analysis.api import api_router
from test_analysis.api.errors import register_error_handlers
from test_analysis.config import get_settings
from test_analysis.patient_card import create_schema, get_session_factory
from test_analysis.seed import seed_if_empty

# static export of the Next.js UI (`npm run build` in frontend/), relative to the working directory
FRONTEND_DIR = Path("frontend/out")


class FrontendFiles(StaticFiles):
    """Static UI that leaves unknown /api paths to the JSON error handler instead of 404.html."""

    async def get_response(self, path: str, scope: Scope) -> Response:
        if path == "api" or path.startswith("api/"):
            raise HTTPException(status_code=404, detail=f"no API route {scope['path']}")
        return await super().get_response(path, scope)


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
    # mounted last so that /api routes win; absent until the frontend is built
    if FRONTEND_DIR.is_dir():
        application.mount("/", FrontendFiles(directory=FRONTEND_DIR, html=True), name="frontend")
    return application


app = create_app()
