"""Extraction contract: answer schema, fake extractor fixtures and extractor choice (R8, R10)."""

import hashlib
import json
from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError

from scan_files import SAMPLES_DIR
from test_analysis.config import Settings
from test_analysis.extraction import (
    ExtractionResult,
    FakeExtractor,
    OpenRouterExtractor,
    get_extractor,
)
from test_analysis.extraction.fake import FIXTURES_DIR

VALID_ITEM = {
    "test_name_raw": "Гемоглобин",
    "value": 128.0,
    "value_raw": "128",
    "unit": "г/л",
    "ref_range": "120-140",
    "flag": "normal",
    "confidence": 0.97,
    "needs_review": False,
}


def test_schema_accepts_valid_item_with_nullable_fields() -> None:
    item = {**VALID_ITEM, "value": None, "unit": None, "ref_range": None, "flag": None}

    result = ExtractionResult.model_validate({"items": [VALID_ITEM, item]})

    assert len(result.items) == 2
    assert result.items[1].value is None


def test_schema_accepts_empty_items() -> None:
    assert ExtractionResult.model_validate_json('{"items": []}').items == []


@pytest.mark.parametrize(
    "change",
    [
        {"confidence": 1.5},
        {"confidence": -0.1},
        {"flag": "unknown"},
        {"flag": "HIGH"},
        {"value": "много"},
        {"extra_field": 1},
    ],
)
def test_schema_rejects_invalid_item(change: dict) -> None:
    with pytest.raises(ValidationError):
        ExtractionResult.model_validate({"items": [{**VALID_ITEM, **change}]})


@pytest.mark.parametrize(
    "field", ["test_name_raw", "value", "value_raw", "unit", "flag", "confidence"]
)
def test_schema_rejects_missing_required_field(field: str) -> None:
    item = {key: value for key, value in VALID_ITEM.items() if key != field}

    with pytest.raises(ValidationError):
        ExtractionResult.model_validate({"items": [item]})


def test_schema_json_schema_is_strict_compatible() -> None:
    schema = ExtractionResult.model_json_schema()
    item_schema = schema["$defs"]["ExtractedItem"]

    assert schema["additionalProperties"] is False
    assert item_schema["additionalProperties"] is False
    assert set(item_schema["required"]) == set(VALID_ITEM)


def test_fake_extractor_without_matching_fixture_returns_default() -> None:
    expected = ExtractionResult.model_validate_json((FIXTURES_DIR / "default.json").read_bytes())

    result = FakeExtractor().extract([], source=b"bytes without fixture")

    assert result == expected
    assert FakeExtractor().model_id == "fake"


@pytest.mark.parametrize(
    ("name", "first_name_raw"),
    [
        ("cbc_ivanova.pdf", "Гемоглобин (HGB)"),
        ("biochem_petrov.jpg", "Глюкоза"),
        ("mixed_sidorova.png", "Hb"),
    ],
)
def test_fake_extractor_demo_sample_returns_its_fixture(name: str, first_name_raw: str) -> None:
    source = (SAMPLES_DIR / name).read_bytes()
    assert (FIXTURES_DIR / f"{hashlib.sha256(source).hexdigest()}.json").is_file()

    result = FakeExtractor().extract([], source=source)

    assert result.items[0].test_name_raw == first_name_raw


def test_fake_extractor_fixture_is_chosen_by_sha256(tmp_path: Path) -> None:
    source = b"custom scan"
    item = {**VALID_ITEM, "test_name_raw": "custom"}
    (tmp_path / f"{hashlib.sha256(source).hexdigest()}.json").write_text(
        json.dumps({"items": [item]})
    )
    (tmp_path / "default.json").write_text('{"items": []}')
    extractor = FakeExtractor(fixtures_dir=tmp_path)

    assert extractor.extract([], source=source).items[0].test_name_raw == "custom"
    assert extractor.extract([], source=b"other").items == []


def test_demo_fixtures_contain_review_triggers() -> None:
    items = [
        item
        for path in FIXTURES_DIR.glob("*.json")
        if path.name != "default.json"
        for item in ExtractionResult.model_validate_json(path.read_bytes()).items
    ]

    assert any(item.confidence < 0.8 for item in items)
    assert any(item.test_name_raw == "ГЛЮ" for item in items)


def test_get_extractor_fake_mode_returns_fake() -> None:
    assert isinstance(get_extractor(Settings(_env_file=None, extractor="fake")), FakeExtractor)


def test_get_extractor_openrouter_mode_uses_configured_model() -> None:
    settings = Settings(
        _env_file=None,
        extractor="openrouter",
        openrouter_api_key=SecretStr("sk-test"),
        openrouter_model="vendor/vision-model",
    )

    extractor = get_extractor(settings)

    assert isinstance(extractor, OpenRouterExtractor)
    assert extractor.model_id == "vendor/vision-model"
