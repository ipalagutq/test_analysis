"""Normalization of extracted items into review draft rows (R11)."""

import pytest

from test_analysis.extraction import ExtractedItem, ExtractionResult, normalize


def _item(**changes: object) -> ExtractedItem:
    fields = {
        "test_name_raw": "Гемоглобин",
        "value": 128.0,
        "value_raw": "128",
        "unit": "г/л",
        "ref_range": "120-140",
        "flag": "normal",
        "confidence": 0.97,
        "needs_review": False,
    }
    return ExtractedItem.model_validate({**fields, **changes})


def _rows(*items: ExtractedItem, sex: str = "F") -> list:
    return normalize(ExtractionResult(items=list(items)), sex)


def test_normalize_clean_item_maps_all_fields() -> None:
    (row,) = _rows(_item())

    assert row.model_dump() == {
        "row_id": 0,
        "test_name_raw": "Гемоглобин",
        "value_raw": "128",
        "value": 128.0,
        "unit_raw": "г/л",
        "code": "HGB",
        "canonical_value": 128.0,
        "canonical_unit": "г/л",
        "flag": "normal",
        "llm_flag": "normal",
        "ref_range_raw": "120-140",
        "confidence": 0.97,
        "needs_review": False,
        "include": True,
    }


def test_normalize_row_ids_follow_item_order() -> None:
    rows = _rows(_item(), _item(test_name_raw="Glucose", value=5.0, unit="ммоль/л"), _item())

    assert [row.row_id for row in rows] == [0, 1, 2]
    assert [row.code for row in rows] == ["HGB", "GLU", "HGB"]


def test_normalize_empty_result_returns_no_rows() -> None:
    assert _rows() == []


def test_normalize_converts_unit_and_flags_by_catalog() -> None:
    (row,) = _rows(
        _item(test_name_raw="Глюкоза", value=104.0, value_raw="104", unit="мг/дл", flag="high")
    )

    assert row.code == "GLU"
    assert row.canonical_value == pytest.approx(5.772, abs=0.01)
    assert row.canonical_unit == "ммоль/л"
    assert row.flag == "normal"
    assert row.llm_flag == "high"


def test_normalize_flag_depends_on_patient_sex() -> None:
    item = _item(value=125.0, flag=None)

    assert _rows(item, sex="F")[0].flag == "normal"
    assert _rows(item, sex="M")[0].flag == "low"


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param({"needs_review": True}, id="llm_needs_review"),
        pytest.param({"confidence": 0.79}, id="low_confidence"),
        pytest.param({"test_name_raw": "Показатель Х"}, id="unknown_name"),
        pytest.param({"value": None, "value_raw": "не определено"}, id="no_value"),
        pytest.param({"unit": "furlong"}, id="unknown_unit"),
        pytest.param({"unit": None}, id="no_unit"),
        pytest.param({"flag": "high"}, id="flag_mismatch"),
    ],
)
def test_normalize_each_review_condition_sets_needs_review(changes: dict) -> None:
    (row,) = _rows(_item(**changes))

    assert row.needs_review is True


def test_normalize_confidence_at_threshold_does_not_need_review() -> None:
    assert _rows(_item(confidence=0.8))[0].needs_review is False


def test_normalize_missing_llm_flag_does_not_need_review() -> None:
    assert _rows(_item(flag=None))[0].needs_review is False


def test_normalize_flag_mismatch_ignored_when_catalog_flag_unknown() -> None:
    (row,) = _rows(_item(test_name_raw="Показатель Х", flag="high"))

    assert row.flag == "unknown"
    assert row.code is None


def test_normalize_unknown_name_keeps_raw_reading() -> None:
    (row,) = _rows(_item(test_name_raw="Показатель Х", value=3.2, value_raw="3.2", unit="ед."))

    assert (row.code, row.canonical_value, row.canonical_unit) == (None, None, None)
    assert (row.value, row.value_raw, row.unit_raw) == (3.2, "3.2", "ед.")
    assert row.include is True


def test_normalize_unconvertible_unit_leaves_canonical_value_empty() -> None:
    (row,) = _rows(_item(unit="furlong"))

    assert row.code == "HGB"
    assert (row.canonical_value, row.canonical_unit, row.flag) == (None, None, "unknown")
