"""Patient card tables: demo patients, review drafts, confirmed visits and their results."""

import uuid
from datetime import UTC, date, datetime
from typing import Literal

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

DraftStatus = Literal["draft", "confirmed", "discarded"]


def _now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Declarative base of all patient card tables."""


class Patient(Base):
    """A fictional demo patient; real personal data is never stored."""

    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True)
    display_name: Mapped[str]
    sex: Mapped[str] = mapped_column(String(1))
    birth_year: Mapped[int]
    is_demo: Mapped[bool] = mapped_column(default=True)

    visits: Mapped[list["Visit"]] = relationship(back_populates="patient")


class Draft(Base):
    """An extraction awaiting human review; rows are `DraftRow` dumps."""

    __tablename__ = "drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    status: Mapped[str] = mapped_column(String(16), default="draft")
    extractor: Mapped[str]
    model: Mapped[str | None]
    mime: Mapped[str]
    page_count: Mapped[int]
    rows: Mapped[list[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(default=_now)
    decided_at: Mapped[datetime | None]


class Visit(Base):
    """A confirmed lab visit: one collection date with its results."""

    __tablename__ = "visits"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    collected_at: Mapped[date]
    draft_id: Mapped[str | None] = mapped_column(ForeignKey("drafts.id"))
    model: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(default=_now)

    patient: Mapped[Patient] = relationship(back_populates="visits")
    results: Mapped[list["Result"]] = relationship(
        back_populates="visit", cascade="all, delete-orphan", order_by="Result.id"
    )


class Result(Base):
    """One confirmed test value in the canonical unit with its catalog flag."""

    __tablename__ = "results"

    id: Mapped[int] = mapped_column(primary_key=True)
    visit_id: Mapped[int] = mapped_column(ForeignKey("visits.id"))
    code: Mapped[str] = mapped_column(String(16), index=True)
    value: Mapped[float]
    unit: Mapped[str]
    flag: Mapped[str] = mapped_column(String(8))
    test_name_raw: Mapped[str | None]

    visit: Mapped[Visit] = relationship(back_populates="results")
