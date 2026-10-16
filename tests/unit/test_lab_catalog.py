"""Lab catalog: file validation, name matching, unit conversion and flags (R3–R6)."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from test_analysis.lab_catalog import (
    LabCatalog,
    ReferenceInterval,
    compute_flag,
    convert,
    get_catalog,
    load_catalog,
    match,
)
from test_analysis.lab_catalog.catalog import CATALOG_PATH, normalize_name


@pytest.fixture
def catalog_data() -> dict:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def test_catalog_file_loads_within_size_limits() -> None:
    catalog = load_catalog(CATALOG_PATH)

    assert 30 <= len(catalog.tests) <= 50
    assert {test.group for test in catalog.tests} == {"cbc", "biochem"}


def test_catalog_file_entries_have_synonyms_and_reference_for_both_sexes() -> None:
    for test in get_catalog().tests:
        assert len(test.synonyms) >= 2, test.code
        assert test.reference_for("M") is not None, test.code
        assert test.reference_for("F") is not None, test.code


def test_catalog_synonym_shared_by_two_codes_is_rejected(catalog_data: dict) -> None:
    first, second = catalog_data["tests"][0], catalog_data["tests"][1]
    second["synonyms"].append(first["synonyms"][0])

    with pytest.raises(ValidationError, match="shared by"):
        LabCatalog.model_validate(catalog_data)


def test_catalog_synonym_differing_only_by_noise_is_rejected(catalog_data: dict) -> None:
    first, second = catalog_data["tests"][0], catalog_data["tests"][1]
    second["synonyms"].append(f" {first['name_ru'].upper()}. ")

    with pytest.raises(ValidationError, match="shared by"):
        LabCatalog.model_validate(catalog_data)


def test_catalog_duplicate_code_is_rejected(catalog_data: dict) -> None:
    catalog_data["tests"].append(catalog_data["tests"][0])

    with pytest.raises(ValidationError, match="duplicate code"):
        LabCatalog.model_validate(catalog_data)


def test_catalog_with_too_few_tests_is_rejected(catalog_data: dict) -> None:
    catalog_data["tests"] = catalog_data["tests"][:29]

    with pytest.raises(ValidationError):
        LabCatalog.model_validate(catalog_data)


def test_catalog_test_without_reference_is_rejected(catalog_data: dict) -> None:
    test = catalog_data["tests"][0]
    for key in ("ref", "ref_male", "ref_female"):
        test.pop(key, None)

    with pytest.raises(ValidationError, match="needs `ref`"):
        LabCatalog.model_validate(catalog_data)


def test_catalog_conflicting_unit_factors_are_rejected(catalog_data: dict) -> None:
    hgb = next(test for test in catalog_data["tests"] if test["code"] == "HGB")
    hgb["unit_aliases"]["G/DL"] = 1

    with pytest.raises(ValidationError, match="conflicting factors"):
        LabCatalog.model_validate(catalog_data)


@pytest.mark.parametrize(
    ("low", "high"),
    [(None, None), (5.0, 1.0)],
)
def test_reference_interval_invalid_bounds_are_rejected(
    low: float | None, high: float | None
) -> None:
    with pytest.raises(ValidationError):
        ReferenceInterval(low=low, high=high)


@pytest.mark.parametrize(
    ("name_raw", "code"),
    [
        ("Hb", "HGB"),
        ("HGB", "HGB"),
        ("Гемоглобин", "HGB"),
        ("гемоглобин", "HGB"),
        ("Гемоглобин (HGB)", "HGB"),
        ("  hgb. ", "HGB"),
        ("Glucose", "GLU"),
        ("Креатинин", "CREA"),
        ("Холестерин общий", "CHOL"),
        ("АЛТ", "ALT"),
    ],
)
def test_match_known_spelling_returns_canonical_code(name_raw: str, code: str) -> None:
    assert match(name_raw) == code


@pytest.mark.parametrize("name_raw", ["Показатель Х", "ГЛЮ", "", "Гемоглобинн"])
def test_match_unknown_spelling_returns_none(name_raw: str) -> None:
    assert match(name_raw) is None


def test_normalize_name_drops_case_yo_and_punctuation() -> None:
    assert normalize_name("Мочевая Кислота (ёЁ)-.") == normalize_name("мочеваякислотаее")


@pytest.mark.parametrize(
    ("code", "value", "unit", "expected_value", "expected_unit"),
    [
        ("GLU", 104.0, "мг/дл", 5.772, "ммоль/л"),
        ("GLU", 5.5, "ммоль/л", 5.5, "ммоль/л"),
        ("GLU", 90.0, "mg/dL", 4.995, "ммоль/л"),
        ("CREA", 1.0, "мг/дл", 88.42, "мкмоль/л"),
        ("CREA", 70.0, "µmol/L", 70.0, "мкмоль/л"),
        ("CREA", 70.0, "мкмоль / л", 70.0, "мкмоль/л"),
        ("HGB", 14.8, "г/дл", 148.0, "г/л"),
        ("HGB", 14.8, "g/dl", 148.0, "г/л"),
        ("CHOL", 200.0, "мг/дл", 5.172, "ммоль/л"),
    ],
)
def test_convert_known_unit_returns_canonical_value(
    code: str, value: float, unit: str, expected_value: float, expected_unit: str
) -> None:
    result = convert(code, value, unit)

    assert result is not None
    assert result[0] == pytest.approx(expected_value, abs=0.01)
    assert result[1] == expected_unit


@pytest.mark.parametrize(
    ("code", "unit"),
    [("HGB", "furlong"), ("HGB", None), ("NOPE", "г/л"), ("GLU", "мкмоль/л")],
)
def test_convert_unknown_code_or_unit_returns_none(code: str, unit: str | None) -> None:
    assert convert(code, 1.0, unit) is None


@pytest.mark.parametrize(
    ("code", "value", "sex", "flag"),
    [
        ("HGB", 119.9, "F", "low"),
        ("HGB", 120.0, "F", "normal"),
        ("HGB", 150.0, "F", "normal"),
        ("HGB", 150.1, "F", "high"),
        ("HGB", 125.0, "M", "low"),
        ("HGB", 125.0, "F", "normal"),
        ("GLU", 3.8, "M", "low"),
        ("GLU", 6.2, "F", "high"),
        ("ALT", 0.0, "M", "normal"),
        ("ALT", 41.0, "M", "normal"),
        ("ALT", 41.0, "F", "high"),
        ("CHOL", 5.3, "M", "high"),
    ],
)
def test_compute_flag_compares_with_sex_specific_interval(
    code: str, value: float, sex: str, flag: str
) -> None:
    assert compute_flag(code, value, sex) == flag


def test_compute_flag_unknown_code_returns_unknown() -> None:
    assert compute_flag("NOPE", 1.0, "M") == "unknown"


def test_get_catalog_is_loaded_once() -> None:
    assert get_catalog() is get_catalog()


def test_load_catalog_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_catalog(tmp_path / "missing.json")
