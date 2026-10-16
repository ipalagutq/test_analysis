"""Patient card repository and demo seed on a temporary SQLite database (R14, R15, R17, R18)."""

import json
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from test_analysis.extraction import DraftRow
from test_analysis.patient_card import (
    ConfirmRow,
    Draft,
    DraftNotFoundError,
    DraftStatusConflictError,
    InvalidConfirmRowsError,
    Patient,
    PatientNotFoundError,
    Result,
    UnknownTestCodeError,
    Visit,
    confirm_draft,
    create_draft,
    discard_draft,
    get_draft,
    list_patients,
    timeline,
    trend,
)
from test_analysis.seed import SEED_PATH, seed_demo, seed_if_empty


def _count(session: Session, table: type) -> int:
    return session.scalar(select(func.count()).select_from(table)) or 0


def _draft_row(row_id: int, test_name_raw: str, code: str | None, value: float | None) -> DraftRow:
    return DraftRow(
        row_id=row_id,
        test_name_raw=test_name_raw,
        value_raw=str(value),
        value=value,
        unit_raw="г/л",
        code=code,
        canonical_value=value,
        canonical_unit="г/л" if code else None,
        flag="unknown",
        llm_flag=None,
        ref_range_raw=None,
        confidence=0.9,
        needs_review=code is None,
    )


@pytest.fixture
def seeded(session: Session) -> Session:
    seed_demo(session)
    return session


@pytest.fixture
def draft(seeded: Session) -> Draft:
    # patient 1 is female: HGB 125 is normal for F, PLT 500 is high
    return create_draft(
        seeded,
        patient_id=1,
        extractor="fake",
        model="fake",
        mime="image/png",
        page_count=1,
        rows=[
            _draft_row(0, "Hb", "HGB", 125.0),
            _draft_row(1, "Тромбоциты", "PLT", 500.0),
            _draft_row(2, "Показатель Х", None, 3.2),
        ],
    )


def test_seed_creates_three_demo_patients_with_visits(session: Session) -> None:
    added = seed_demo(session)

    patients = list_patients(session)
    assert added == 3
    assert len(patients) == 3
    assert all(patient.is_demo and "(демо)" in patient.display_name for patient in patients)
    assert _count(session, Visit) == 7
    for patient in patients:
        assert 2 <= len(patient.visits) <= 3
        assert all(len(visit.results) >= 8 for visit in patient.visits)


def test_seed_twice_does_not_duplicate(session: Session) -> None:
    seed_demo(session)
    counts = (_count(session, Patient), _count(session, Visit), _count(session, Result))

    assert seed_demo(session) == 0
    assert (_count(session, Patient), _count(session, Visit), _count(session, Result)) == counts


def test_seed_results_use_catalog_units_and_flags(seeded: Session) -> None:
    # Иванова (F), first visit: HGB 104 is below the female range
    hgb = seeded.scalars(
        select(Result)
        .join(Result.visit)
        .where(Visit.patient_id == 1, Result.code == "HGB")
        .order_by(Visit.collected_at)
    ).first()

    assert hgb is not None
    assert (hgb.value, hgb.unit, hgb.flag) == (104, "г/л", "low")


def test_seed_if_empty_skips_non_empty_card(seeded: Session) -> None:
    assert seed_if_empty(seeded) == 0
    assert _count(seeded, Patient) == 3


def test_seed_unknown_code_is_rejected(session: Session, tmp_path: Path) -> None:
    data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    results = data["patients"][0]["visits"][0]["results"]
    results["NOPE"] = 1.0
    path = tmp_path / "patients.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match="NOPE"):
        seed_demo(session, path=path)


def test_create_draft_writes_no_results(seeded: Session, draft: Draft) -> None:
    results_before = _count(seeded, Result)

    stored = get_draft(seeded, draft.id)

    assert stored.status == "draft"
    assert [row["code"] for row in stored.rows] == ["HGB", "PLT", None]
    assert _count(seeded, Result) == results_before


def test_create_draft_unknown_patient_raises(seeded: Session) -> None:
    with pytest.raises(PatientNotFoundError):
        create_draft(
            seeded, patient_id=999, extractor="fake", model="fake", mime="image/png",
            page_count=1, rows=[],
        )  # fmt: skip


def test_get_draft_unknown_id_raises(seeded: Session) -> None:
    with pytest.raises(DraftNotFoundError):
        get_draft(seeded, "missing")


def test_confirm_writes_only_included_rows_with_recomputed_flags(
    seeded: Session, draft: Draft
) -> None:
    visit = confirm_draft(
        seeded,
        draft.id,
        collected_at=date(2026, 10, 1),
        rows=[
            ConfirmRow(row_id=0, code="HGB", canonical_value=125.0, include=True),
            ConfirmRow(row_id=1, code="PLT", canonical_value=500.0, include=True),
            ConfirmRow(row_id=2, code=None, canonical_value=3.2, include=False),
        ],
    )

    stored = seeded.get(Visit, visit.id)
    assert stored is not None
    assert (stored.patient_id, stored.collected_at, stored.draft_id, stored.model) == (
        1, date(2026, 10, 1), draft.id, "fake",
    )  # fmt: skip
    assert [(r.code, r.value, r.unit, r.flag, r.test_name_raw) for r in stored.results] == [
        ("HGB", 125.0, "г/л", "normal", "Hb"),
        ("PLT", 500.0, "10^9/л", "high", "Тромбоциты"),
    ]
    assert get_draft(seeded, draft.id).status == "confirmed"
    assert get_draft(seeded, draft.id).decided_at is not None


def test_confirm_reviewer_can_assign_code_to_unknown_row(seeded: Session, draft: Draft) -> None:
    visit = confirm_draft(
        seeded,
        draft.id,
        collected_at=date(2026, 10, 1),
        rows=[ConfirmRow(row_id=2, code="CRP", canonical_value=3.2, include=True)],
    )

    assert [(r.code, r.unit, r.test_name_raw) for r in visit.results] == [
        ("CRP", "мг/л", "Показатель Х")
    ]


@pytest.mark.parametrize(
    ("rows", "invalid_row_ids"),
    [
        pytest.param(
            [ConfirmRow(row_id=2, code=None, canonical_value=3.2, include=True)], [2], id="no_code"
        ),
        pytest.param(
            [ConfirmRow(row_id=0, code="NOPE", canonical_value=1.0, include=True)],
            [0],
            id="unknown_code",
        ),
        pytest.param(
            [ConfirmRow(row_id=0, code="HGB", canonical_value=None, include=True)],
            [0],
            id="no_value",
        ),
        pytest.param(
            [ConfirmRow(row_id=7, code="HGB", canonical_value=1.0, include=True)],
            [7],
            id="unknown_row",
        ),
        pytest.param(
            [
                ConfirmRow(row_id=0, code="HGB", canonical_value=125.0, include=True),
                ConfirmRow(row_id=0, code="HGB", canonical_value=126.0, include=True),
            ],
            [0],
            id="duplicate_row",
        ),
        pytest.param(
            [
                ConfirmRow(row_id=1, code="PLT", canonical_value=None, include=True),
                ConfirmRow(row_id=0, code="HGB", canonical_value=125.0, include=True),
                ConfirmRow(row_id=2, code=None, canonical_value=3.2, include=True),
            ],
            [1, 2],
            id="valid_and_invalid_mixed",
        ),
    ],
)
def test_confirm_invalid_rows_write_nothing(
    seeded: Session, draft: Draft, rows: list[ConfirmRow], invalid_row_ids: list[int]
) -> None:
    counts = (_count(seeded, Visit), _count(seeded, Result))

    with pytest.raises(InvalidConfirmRowsError) as error:
        confirm_draft(seeded, draft.id, collected_at=date(2026, 10, 1), rows=rows)

    assert error.value.row_ids == invalid_row_ids
    seeded.rollback()
    assert (_count(seeded, Visit), _count(seeded, Result)) == counts
    assert get_draft(seeded, draft.id).status == "draft"


def test_confirm_excluded_invalid_row_is_ignored(seeded: Session, draft: Draft) -> None:
    visit = confirm_draft(
        seeded,
        draft.id,
        collected_at=date(2026, 10, 1),
        rows=[ConfirmRow(row_id=2, code=None, canonical_value=None, include=False)],
    )

    assert visit.results == []


@pytest.mark.parametrize("first_decision", ["confirm", "discard"])
@pytest.mark.parametrize("second_decision", ["confirm", "discard"])
def test_decided_draft_cannot_be_decided_again(
    seeded: Session, draft: Draft, first_decision: str, second_decision: str
) -> None:
    def decide(decision: str) -> None:
        if decision == "confirm":
            confirm_draft(seeded, draft.id, collected_at=date(2026, 10, 1), rows=[])
        else:
            discard_draft(seeded, draft.id)

    decide(first_decision)
    visits = _count(seeded, Visit)

    with pytest.raises(DraftStatusConflictError):
        decide(second_decision)

    assert _count(seeded, Visit) == visits


def test_discard_marks_draft_and_leaves_card(seeded: Session, draft: Draft) -> None:
    counts = (_count(seeded, Visit), _count(seeded, Result))

    discarded = discard_draft(seeded, draft.id)

    assert discarded.status == "discarded"
    assert discarded.decided_at is not None
    assert (_count(seeded, Visit), _count(seeded, Result)) == counts


def test_timeline_lists_visits_newest_first_with_names(seeded: Session) -> None:
    visits = timeline(seeded, 1)

    assert [visit.collected_at for visit in visits] == [
        date(2026, 8, 5), date(2026, 3, 18), date(2025, 11, 12),
    ]  # fmt: skip
    hgb = next(result for result in visits[0].results if result.code == "HGB")
    assert (hgb.name_ru, hgb.value, hgb.unit, hgb.flag) == ("Гемоглобин", 128, "г/л", "normal")


def test_timeline_includes_confirmed_visit(seeded: Session, draft: Draft) -> None:
    confirm_draft(
        seeded,
        draft.id,
        collected_at=date(2026, 10, 1),
        rows=[ConfirmRow(row_id=0, code="HGB", canonical_value=125.0, include=True)],
    )

    newest = timeline(seeded, 1)[0]

    assert newest.collected_at == date(2026, 10, 1)
    assert newest.model == "fake"
    assert [result.code for result in newest.results] == ["HGB"]


def test_timeline_unknown_patient_raises(seeded: Session) -> None:
    with pytest.raises(PatientNotFoundError):
        timeline(seeded, 999)


def test_trend_returns_points_oldest_first_with_sex_reference(seeded: Session) -> None:
    result = trend(seeded, 1, "HGB")

    assert (result.code, result.unit, result.ref_low, result.ref_high) == ("HGB", "г/л", 120, 150)
    assert [(p.collected_at, p.value, p.flag) for p in result.points] == [
        (date(2025, 11, 12), 104, "low"),
        (date(2026, 3, 18), 116, "low"),
        (date(2026, 8, 5), 128, "normal"),
    ]


def test_trend_open_reference_bound_is_none(seeded: Session) -> None:
    result = trend(seeded, 2, "ALT")

    assert (result.ref_low, result.ref_high) == (None, 41)


def test_trend_code_without_values_returns_no_points(seeded: Session) -> None:
    assert trend(seeded, 1, "GLU").points == []


def test_trend_unknown_code_raises(seeded: Session) -> None:
    with pytest.raises(UnknownTestCodeError):
        trend(seeded, 1, "NOPE")


def test_trend_unknown_patient_raises(seeded: Session) -> None:
    with pytest.raises(PatientNotFoundError):
        trend(seeded, 999, "HGB")
