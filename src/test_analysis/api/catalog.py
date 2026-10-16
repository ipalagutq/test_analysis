"""Lab catalog route for the review UI."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from test_analysis.lab_catalog import LabCatalog, get_catalog
from test_analysis.lab_catalog.models import TestGroup

router = APIRouter()


class CatalogEntry(BaseModel):
    code: str
    name_ru: str
    unit: str
    group: TestGroup


@router.get("/catalog")
def read_catalog(catalog: Annotated[LabCatalog, Depends(get_catalog)]) -> list[CatalogEntry]:
    """List catalog tests for code selection on the review screen."""
    return [
        CatalogEntry(code=test.code, name_ru=test.name_ru, unit=test.unit, group=test.group)
        for test in catalog.tests
    ]
