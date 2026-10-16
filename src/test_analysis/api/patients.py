"""Patient card routes: demo patients, visit timeline and test trends."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from test_analysis.lab_catalog import Sex
from test_analysis.patient_card import (
    TimelineVisit,
    Trend,
    get_session,
    list_patients,
    timeline,
    trend,
)

router = APIRouter()


class PatientView(BaseModel):
    id: int
    display_name: str
    sex: Sex
    birth_year: int


@router.get("/patients")
def read_patients(session: Annotated[Session, Depends(get_session)]) -> list[PatientView]:
    """List demo patients for selection on the upload screen."""
    return [
        PatientView(
            id=patient.id,
            display_name=patient.display_name,
            sex=patient.sex,
            birth_year=patient.birth_year,
        )
        for patient in list_patients(session)
    ]


@router.get("/patients/{patient_id}/timeline")
def read_timeline(
    patient_id: int, session: Annotated[Session, Depends(get_session)]
) -> list[TimelineVisit]:
    """Return the patient's visits, newest first."""
    return timeline(session, patient_id)


@router.get("/patients/{patient_id}/trends")
def read_trend(
    patient_id: int, code: str, session: Annotated[Session, Depends(get_session)]
) -> Trend:
    """Return one test's values across visits, oldest first."""
    return trend(session, patient_id, code)
