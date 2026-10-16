"""Scan upload route: preprocessing, extraction and normalization into a review draft."""

from pathlib import Path
from typing import Annotated, cast

from fastapi import APIRouter, Depends, Form, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from test_analysis.config import Settings, get_settings
from test_analysis.extraction import Extractor, ScanPages, get_extractor, normalize, preprocess
from test_analysis.lab_catalog import Sex
from test_analysis.patient_card import create_draft, get_patient, get_session

router = APIRouter()

_EXTENSION_BY_MIME = {"application/pdf": "pdf", "image/jpeg": "jpg", "image/png": "png"}


class UploadCreated(BaseModel):
    draft_id: str


def get_request_extractor(settings: Annotated[Settings, Depends(get_settings)]) -> Extractor:
    """Return the configured extractor; FastAPI dependency, overridable in tests."""
    return get_extractor(settings)


def page_path(upload_dir: str, draft_id: str, page_number: int) -> Path:
    """Return where the PNG of a draft page is stored."""
    return Path(upload_dir) / draft_id / f"page_{page_number}.png"


# plain `def`: preprocessing and the LLM call block, FastAPI runs it in the threadpool
@router.post("/uploads", status_code=status.HTTP_201_CREATED)
def create_upload(
    file: UploadFile,
    patient_id: Annotated[int, Form()],
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    extractor: Annotated[Extractor, Depends(get_request_extractor)],
) -> UploadCreated:
    """Read a scan into a draft awaiting review; the patient card is not touched."""
    # unknown patient fails before the paid LLM call
    patient = get_patient(session, patient_id)
    source = file.file.read()
    scan = preprocess(source)
    result = extractor.extract(scan.pages, source=source)
    rows = normalize(result, cast(Sex, patient.sex))
    draft = create_draft(
        session,
        patient_id=patient_id,
        extractor=settings.extractor,
        model=extractor.model_id,
        mime=scan.mime,
        page_count=len(scan.pages),
        rows=rows,
    )
    try:
        _store_scan(settings.upload_dir, draft.id, source, scan)
    except OSError:
        # a draft without its pages cannot be reviewed
        session.delete(draft)
        session.commit()
        raise
    return UploadCreated(draft_id=draft.id)


def _store_scan(upload_dir: str, draft_id: str, source: bytes, scan: ScanPages) -> None:
    draft_dir = Path(upload_dir) / draft_id
    draft_dir.mkdir(parents=True, exist_ok=True)
    (draft_dir / f"original.{_EXTENSION_BY_MIME[scan.mime]}").write_bytes(source)
    for page_number, page in enumerate(scan.pages):
        page_path(upload_dir, draft_id, page_number).write_bytes(page)
