"""Structured answer the vision-LLM must return for one scan."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

LlmFlag = Literal["low", "normal", "high"]


class ExtractedItem(BaseModel):
    """One lab result row exactly as read from the scan, before catalog normalization."""

    # strict json_schema needs every field required and no extra properties
    model_config = ConfigDict(frozen=True, extra="forbid")

    test_name_raw: str
    value: float | None
    value_raw: str
    unit: str | None
    ref_range: str | None
    flag: LlmFlag | None
    confidence: float = Field(ge=0, le=1)
    needs_review: bool


class ExtractionResult(BaseModel):
    """All lab result rows read from one scan."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    items: list[ExtractedItem]
