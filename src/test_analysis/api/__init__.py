"""HTTP routes mounted under /api."""

from fastapi import APIRouter

from test_analysis.api.catalog import router as catalog_router
from test_analysis.api.drafts import router as drafts_router
from test_analysis.api.health import router as health_router
from test_analysis.api.patients import router as patients_router
from test_analysis.api.uploads import router as uploads_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(catalog_router)
api_router.include_router(patients_router)
api_router.include_router(uploads_router)
api_router.include_router(drafts_router)
