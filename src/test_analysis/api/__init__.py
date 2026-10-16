"""HTTP routes mounted under /api."""

from fastapi import APIRouter

from test_analysis.api.health import router as health_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
