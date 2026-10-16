"""Database engine, sessions and schema creation for the patient card."""

import sqlite3
from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from test_analysis.config import get_settings
from test_analysis.patient_card.models import Base


@lru_cache
def get_engine() -> Engine:
    """Return the process-wide engine for `DATABASE_URL`."""
    url = make_url(get_settings().database_url)
    if url.get_backend_name() != "sqlite":
        return create_engine(url)
    if url.database and url.database != ":memory:":
        Path(url.database).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, connect_args={"check_same_thread": False})
    event.listen(engine, "connect", _enable_sqlite_foreign_keys)
    return engine


def _enable_sqlite_foreign_keys(connection: sqlite3.Connection, record: object) -> None:
    connection.execute("PRAGMA foreign_keys=ON")


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    """Return the session factory bound to the process-wide engine."""
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def create_schema() -> None:
    """Create missing tables; the demo has no migrations."""
    Base.metadata.create_all(get_engine())


def get_session() -> Iterator[Session]:
    """Yield a session per request; FastAPI dependency."""
    with get_session_factory()() as session:
        yield session
