"""Idempotent seed of fictional demo patients with visits; `python -m test_analysis.seed`."""

from datetime import date
from pathlib import Path

from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from test_analysis.lab_catalog import LabCatalog, Sex, get_catalog
from test_analysis.patient_card import Patient, Result, Visit, create_schema, get_session_factory

SEED_PATH = Path("data/seed/patients.json")


class SeedVisit(BaseModel):
    collected_at: date
    results: dict[str, float] = Field(min_length=8)


class SeedPatient(BaseModel):
    id: int
    display_name: str
    sex: Sex
    birth_year: int
    visits: list[SeedVisit] = Field(min_length=2, max_length=3)


class SeedData(BaseModel):
    patients: list[SeedPatient]


def seed_demo(
    session: Session, *, path: Path = SEED_PATH, catalog: LabCatalog | None = None
) -> int:
    """Add missing demo patients with their visits; return how many patients were added."""
    catalog = catalog or get_catalog()
    seed = SeedData.model_validate_json(path.read_bytes())
    added = 0
    for seed_patient in seed.patients:
        if session.get(Patient, seed_patient.id) is not None:
            continue
        session.add(_demo_patient(seed_patient, catalog))
        added += 1
    session.commit()
    return added


def seed_if_empty(session: Session) -> int:
    """Seed the demo patients only when the patient card has no patients yet."""
    if session.scalar(select(func.count()).select_from(Patient)):
        return 0
    return seed_demo(session)


def _demo_patient(seed_patient: SeedPatient, catalog: LabCatalog) -> Patient:
    patient = Patient(
        id=seed_patient.id,
        display_name=seed_patient.display_name,
        sex=seed_patient.sex,
        birth_year=seed_patient.birth_year,
        is_demo=True,
    )
    for seed_visit in seed_patient.visits:
        visit = Visit(collected_at=seed_visit.collected_at, model=None)
        for code, value in seed_visit.results.items():
            test = catalog.find(code)
            if test is None:
                raise ValueError(f"seed patient {seed_patient.id}: unknown test code {code}")
            visit.results.append(
                Result(
                    code=code,
                    value=value,
                    unit=test.unit,
                    flag=catalog.compute_flag(code, value, seed_patient.sex),
                    test_name_raw=None,
                )
            )
        patient.visits.append(visit)
    return patient


def main() -> None:
    """Create the schema and add the demo patients that are missing."""
    create_schema()
    with get_session_factory()() as session:
        added = seed_demo(session)
        patients = session.scalar(select(func.count()).select_from(Patient))
        visits = session.scalar(select(func.count()).select_from(Visit))
    print(f"seed: added {added} patients; total {patients} patients, {visits} visits")


if __name__ == "__main__":
    main()
