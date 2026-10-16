"""Patient card operations: draft lifecycle, confirmation into visits, timeline and trends."""

from datetime import UTC, date, datetime
from typing import cast

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from test_analysis.extraction.normalize import DraftRow
from test_analysis.lab_catalog import Flag, LabCatalog, Sex, get_catalog
from test_analysis.patient_card.models import Draft, Patient, Result, Visit


class PatientNotFoundError(LookupError):
    """The patient id is not in the patient card."""


class DraftNotFoundError(LookupError):
    """The draft id is not in the patient card."""


class UnknownTestCodeError(LookupError):
    """The test code is not in the lab catalog."""


class DraftStatusConflictError(Exception):
    """The draft was already confirmed or discarded."""

    def __init__(self, draft_id: str, status: str) -> None:
        super().__init__(f"draft {draft_id} is already {status}")
        self.status = status


class InvalidConfirmRowsError(ValueError):
    """Included rows lack a catalog code or a numeric value; nothing was written."""

    def __init__(self, row_ids: list[int]) -> None:
        super().__init__(f"rows without catalog code or numeric value: {row_ids}")
        self.row_ids = row_ids


class ConfirmRow(BaseModel):
    """The reviewer's final decision on one draft row."""

    row_id: int
    code: str | None
    canonical_value: float | None
    include: bool


class TimelineResult(BaseModel):
    code: str
    name_ru: str
    value: float
    unit: str
    flag: Flag


class TimelineVisit(BaseModel):
    visit_id: int
    collected_at: date
    model: str | None
    results: list[TimelineResult]


class TrendPoint(BaseModel):
    collected_at: date
    value: float
    flag: Flag


class Trend(BaseModel):
    code: str
    unit: str
    ref_low: float | None
    ref_high: float | None
    points: list[TrendPoint]


def get_patient(session: Session, patient_id: int) -> Patient:
    """Return the patient or raise `PatientNotFoundError`."""
    patient = session.get(Patient, patient_id)
    if patient is None:
        raise PatientNotFoundError(f"patient {patient_id} not found")
    return patient


def list_patients(session: Session) -> list[Patient]:
    """Return all patients ordered by id."""
    return list(session.scalars(select(Patient).order_by(Patient.id)))


def create_draft(
    session: Session,
    *,
    patient_id: int,
    extractor: str,
    model: str | None,
    mime: str,
    page_count: int,
    rows: list[DraftRow],
) -> Draft:
    """Store normalized rows as a draft awaiting review; nothing reaches `results`."""
    get_patient(session, patient_id)
    draft = Draft(
        patient_id=patient_id,
        extractor=extractor,
        model=model,
        mime=mime,
        page_count=page_count,
        rows=[row.model_dump(mode="json") for row in rows],
    )
    session.add(draft)
    session.commit()
    return draft


def get_draft(session: Session, draft_id: str) -> Draft:
    """Return the draft or raise `DraftNotFoundError`."""
    draft = session.get(Draft, draft_id)
    if draft is None:
        raise DraftNotFoundError(f"draft {draft_id} not found")
    return draft


def confirm_draft(
    session: Session,
    draft_id: str,
    *,
    collected_at: date,
    rows: list[ConfirmRow],
    catalog: LabCatalog | None = None,
) -> Visit:
    """Write a visit with the included rows in one transaction; flags are recomputed."""
    catalog = catalog or get_catalog()
    draft = _get_undecided_draft(session, draft_id)
    sex = cast(Sex, get_patient(session, draft.patient_id).sex)
    stored_rows = {row["row_id"]: DraftRow.model_validate(row) for row in draft.rows}

    visit = Visit(
        patient_id=draft.patient_id, collected_at=collected_at, draft_id=draft.id, model=draft.model
    )
    seen_row_ids: set[int] = set()
    invalid_row_ids: set[int] = set()
    for row in rows:
        if not row.include:
            continue
        test = catalog.find(row.code) if row.code is not None else None
        stored_row = stored_rows.get(row.row_id)
        is_duplicate = row.row_id in seen_row_ids
        seen_row_ids.add(row.row_id)
        if stored_row is None or is_duplicate or test is None or row.canonical_value is None:
            invalid_row_ids.add(row.row_id)
            continue
        visit.results.append(
            Result(
                code=test.code,
                value=row.canonical_value,
                unit=test.unit,
                flag=catalog.compute_flag(test.code, row.canonical_value, sex),
                test_name_raw=stored_row.test_name_raw,
            )
        )
    if invalid_row_ids:
        raise InvalidConfirmRowsError(sorted(invalid_row_ids))

    draft.status = "confirmed"
    draft.decided_at = datetime.now(UTC)
    session.add(visit)
    _commit(session)
    return visit


def discard_draft(session: Session, draft_id: str) -> Draft:
    """Mark the draft as discarded; the patient card is not touched."""
    draft = _get_undecided_draft(session, draft_id)
    draft.status = "discarded"
    draft.decided_at = datetime.now(UTC)
    _commit(session)
    return draft


def timeline(
    session: Session, patient_id: int, *, catalog: LabCatalog | None = None
) -> list[TimelineVisit]:
    """Return the patient's visits, newest first, with their results."""
    catalog = catalog or get_catalog()
    get_patient(session, patient_id)
    visits = session.scalars(
        select(Visit)
        .where(Visit.patient_id == patient_id)
        .order_by(Visit.collected_at.desc(), Visit.id.desc())
        .options(selectinload(Visit.results))
    )
    return [
        TimelineVisit(
            visit_id=visit.id,
            collected_at=visit.collected_at,
            model=visit.model,
            results=[_timeline_result(result, catalog) for result in visit.results],
        )
        for visit in visits
    ]


def trend(
    session: Session, patient_id: int, code: str, *, catalog: LabCatalog | None = None
) -> Trend:
    """Return one test's values across the patient's visits, oldest first."""
    catalog = catalog or get_catalog()
    test = catalog.find(code)
    if test is None:
        raise UnknownTestCodeError(f"test code {code} is not in the catalog")
    patient = get_patient(session, patient_id)
    interval = test.reference_for(cast(Sex, patient.sex))
    rows = session.execute(
        select(Visit.collected_at, Result.value, Result.flag)
        .join(Result.visit)
        .where(Visit.patient_id == patient_id, Result.code == code)
        .order_by(Visit.collected_at, Visit.id)
    )
    return Trend(
        code=code,
        unit=test.unit,
        ref_low=interval.low if interval else None,
        ref_high=interval.high if interval else None,
        points=[
            TrendPoint(collected_at=collected_at, value=value, flag=cast(Flag, flag))
            for collected_at, value, flag in rows
        ],
    )


def _get_undecided_draft(session: Session, draft_id: str) -> Draft:
    draft = get_draft(session, draft_id)
    if draft.status != "draft":
        raise DraftStatusConflictError(draft_id, draft.status)
    return draft


def _commit(session: Session) -> None:
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise


def _timeline_result(result: Result, catalog: LabCatalog) -> TimelineResult:
    test = catalog.find(result.code)
    return TimelineResult(
        code=result.code,
        name_ru=test.name_ru if test else result.code,
        value=result.value,
        unit=result.unit,
        flag=cast(Flag, result.flag),
    )
