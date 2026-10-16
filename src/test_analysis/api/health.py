"""Service health route."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from test_analysis import __version__
from test_analysis.config import Settings, get_settings

router = APIRouter()


class HealthStatus(BaseModel):
    status: Literal["ok"]
    version: str
    extractor: Literal["openrouter", "fake"]


@router.get("/health")
def read_health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthStatus:
    """Report service status, release version and extraction mode."""
    return HealthStatus(status="ok", version=__version__, extractor=settings.extractor)
