"""Settings: defaults, env overrides and the OpenRouter credentials rule (R2, Q4)."""

import pytest
from pydantic import ValidationError

from test_analysis.config import Settings


def test_settings_without_env_use_fake_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.extractor == "fake"
    assert settings.max_upload_mb == 10
    assert settings.max_pdf_pages == 5
    assert settings.llm_timeout_s == 120
    assert settings.openrouter_model is None


def test_settings_env_overrides_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_UPLOAD_MB", "3")
    monkeypatch.setenv("MAX_PDF_PAGES", "2")
    monkeypatch.setenv("LLM_TIMEOUT_S", "30")

    settings = Settings(_env_file=None)

    assert (settings.max_upload_mb, settings.max_pdf_pages, settings.llm_timeout_s) == (3, 2, 30)


@pytest.mark.parametrize(
    ("env", "missing"),
    [
        ({}, ["OPENROUTER_API_KEY", "OPENROUTER_MODEL"]),
        ({"OPENROUTER_MODEL": "vendor/model"}, ["OPENROUTER_API_KEY"]),
        ({"OPENROUTER_API_KEY": "sk-test"}, ["OPENROUTER_MODEL"]),
        ({"OPENROUTER_API_KEY": "", "OPENROUTER_MODEL": "vendor/model"}, ["OPENROUTER_API_KEY"]),
    ],
)
def test_settings_openrouter_without_credentials_fails_naming_missing_vars(
    monkeypatch: pytest.MonkeyPatch, env: dict[str, str], missing: list[str]
) -> None:
    monkeypatch.setenv("EXTRACTOR", "openrouter")
    for name, value in env.items():
        monkeypatch.setenv(name, value)

    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None)

    for name in missing:
        assert name in str(error.value)


def test_settings_openrouter_with_credentials_hides_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EXTRACTOR", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-secret-value")
    monkeypatch.setenv("OPENROUTER_MODEL", "vendor/model")

    settings = Settings(_env_file=None)

    assert settings.openrouter_model == "vendor/model"
    assert "sk-secret-value" not in repr(settings)


@pytest.mark.parametrize("name", ["MAX_UPLOAD_MB", "MAX_PDF_PAGES", "LLM_TIMEOUT_S"])
def test_settings_non_positive_limit_is_rejected(
    monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    monkeypatch.setenv(name, "0")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_unknown_extractor_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EXTRACTOR", "anthropic")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)
