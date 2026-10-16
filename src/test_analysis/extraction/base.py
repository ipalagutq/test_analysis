"""Extractor contract shared by the OpenRouter and fake implementations."""

from typing import Protocol

from test_analysis.extraction.schema import ExtractionResult


# exception names are fixed by the spec (R9, stage 7 error mapping)
class ExtractionFailed(Exception):
    """The LLM call failed: network error, timeout or HTTP error status."""


class ExtractionInvalidResponse(Exception):
    """The LLM answer did not match `ExtractionResult` even after a retry."""


class Extractor(Protocol):
    """Reads lab results from scan pages."""

    @property
    def model_id(self) -> str:
        """Identifier of the model stored with the draft and the visit."""
        ...

    def extract(self, pages: list[bytes], *, source: bytes) -> ExtractionResult:
        """Read lab results from PNG pages; `source` is the original uploaded file."""
        ...
