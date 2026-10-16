"""Shared fixtures: isolated settings and a temporary patient card."""

import os
from collections.abc import Iterator
from pathlib import Path

# tests always run in fake mode, whatever the developer's .env says; set before app import
os.environ["EXTRACTOR"] = "fake"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from test_analysis.config import get_settings
from test_analysis.patient_card import Base, get_engine, get_session_factory

REPO_ROOT = Path(__file__).resolve().parents[1]


def _clear_cached_config() -> None:
    get_settings.cache_clear()
    get_session_factory.cache_clear()
    get_engine.cache_clear()


@pytest.fixture(autouse=True)
def isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Point every test at a temporary database and upload dir, in fake mode, from repo root."""
    monkeypatch.chdir(REPO_ROOT)
    monkeypatch.setenv("EXTRACTOR", "fake")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'patient_card.db'}")
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    _clear_cached_config()
    yield tmp_path
    if get_engine.cache_info().currsize:
        get_engine().dispose()
    _clear_cached_config()


@pytest.fixture
def session(tmp_path: Path) -> Iterator[Session]:
    """A session on an empty patient card schema in a temporary SQLite file."""
    engine = create_engine(f"sqlite:///{tmp_path / 'repo.db'}")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine, expire_on_commit=False)() as db_session:
        yield db_session
    engine.dispose()
