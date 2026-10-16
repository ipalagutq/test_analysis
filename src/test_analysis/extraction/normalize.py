"""Turning raw extraction rows into review draft rows mapped onto the lab catalog."""

from pydantic import BaseModel

from test_analysis.extraction.schema import ExtractedItem, ExtractionResult, LlmFlag
from test_analysis.lab_catalog import Flag, LabCatalog, Sex, get_catalog

MIN_CONFIDENCE = 0.8


class DraftRow(BaseModel):
    """One editable row of a review draft: the scan reading next to its catalog mapping."""

    row_id: int
    test_name_raw: str
    value_raw: str
    value: float | None
    unit_raw: str | None
    code: str | None
    canonical_value: float | None
    canonical_unit: str | None
    flag: Flag
    llm_flag: LlmFlag | None
    ref_range_raw: str | None
    confidence: float
    needs_review: bool
    include: bool = True


def normalize(
    result: ExtractionResult, sex: Sex, *, catalog: LabCatalog | None = None
) -> list[DraftRow]:
    """Map every extracted item onto the catalog; `row_id` is the item's position."""
    catalog = catalog or get_catalog()
    return [_draft_row(row_id, item, sex, catalog) for row_id, item in enumerate(result.items)]


def _draft_row(row_id: int, item: ExtractedItem, sex: Sex, catalog: LabCatalog) -> DraftRow:
    code = catalog.match(item.test_name_raw)
    converted = (
        catalog.convert(code, item.value, item.unit)
        if code is not None and item.value is not None
        else None
    )
    canonical_value, canonical_unit = converted if converted else (None, None)
    flag: Flag = (
        catalog.compute_flag(code, canonical_value, sex)
        if code is not None and canonical_value is not None
        else "unknown"
    )
    has_flag_mismatch = flag != "unknown" and item.flag is not None and item.flag != flag
    needs_review = (
        item.needs_review
        or item.confidence < MIN_CONFIDENCE
        or code is None
        or item.value is None
        or converted is None
        or has_flag_mismatch
    )
    return DraftRow(
        row_id=row_id,
        test_name_raw=item.test_name_raw,
        value_raw=item.value_raw,
        value=item.value,
        unit_raw=item.unit,
        code=code,
        canonical_value=canonical_value,
        canonical_unit=canonical_unit,
        flag=flag,
        llm_flag=item.flag,
        ref_range_raw=item.ref_range,
        confidence=item.confidence,
        needs_review=needs_review,
    )
