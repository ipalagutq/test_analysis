"""Review draft routes: reading, page images, confirmation into the card and discard."""

from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from test_analysis.api.uploads import page_path
from test_analysis.config import Settings, get_settings
from test_analysis.extraction import DraftRow
from test_analysis.patient_card import (
    ConfirmRow,
    Draft,
    DraftStatus,
    confirm_draft,
    discard_draft,
    get_draft,
    get_session,
)

router = APIRouter()


class DraftView(BaseModel):
    id: str
    patient_id: int
    status: DraftStatus
    model: str | None
    extractor: str
    page_count: int
    rows: list[DraftRow]
    created_at: datetime


class ConfirmRequest(BaseModel):
    collected_at: date
    rows: list[ConfirmRow]


class VisitCreated(BaseModel):
    visit_id: int


@router.get("/drafts/{draft_id}")
def read_draft(draft_id: str, session: Annotated[Session, Depends(get_session)]) -> DraftView:
    """Return the draft with its rows for the review screen."""
    return _draft_view(get_draft(session, draft_id))


@router.get(
    "/drafts/{draft_id}/pages/{page_number}",
    response_class=Response,
    responses={200: {"content": {"image/png": {}}}},
)
def read_draft_page(
    draft_id: str,
    page_number: int,
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Response:
    """Return the PNG of a draft page; pages are numbered from 0."""
    draft = get_draft(session, draft_id)
    path = page_path(settings.upload_dir, draft.id, page_number)
    if not 0 <= page_number < draft.page_count or not path.is_file():
        raise HTTPException(status_code=404, detail=f"draft {draft_id} has no page {page_number}")
    return Response(content=path.read_bytes(), media_type="image/png")


@router.post("/drafts/{draft_id}/confirm", status_code=status.HTTP_201_CREATED)
def confirm(
    draft_id: str, request: ConfirmRequest, session: Annotated[Session, Depends(get_session)]
) -> VisitCreated:
    """Write the included rows into a new visit; flags are recomputed by the catalog."""
    visit = confirm_draft(session, draft_id, collected_at=request.collected_at, rows=request.rows)
    return VisitCreated(visit_id=visit.id)


@router.post("/drafts/{draft_id}/discard")
def discard(draft_id: str, session: Annotated[Session, Depends(get_session)]) -> DraftView:
    """Reject the draft; the patient card is not touched."""
    return _draft_view(discard_draft(session, draft_id))


def _draft_view(draft: Draft) -> DraftView:
    return DraftView(
        id=draft.id,
        patient_id=draft.patient_id,
        status=draft.status,
        model=draft.model,
        extractor=draft.extractor,
        page_count=draft.page_count,
        rows=[DraftRow.model_validate(row) for row in draft.rows],
        created_at=draft.created_at,
    )
