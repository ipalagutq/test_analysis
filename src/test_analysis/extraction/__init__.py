"""Scan extraction: file preparation and reading lab results with a vision-LLM."""

from test_analysis.extraction.base import ExtractionFailed, ExtractionInvalidResponse, Extractor
from test_analysis.extraction.factory import get_extractor
from test_analysis.extraction.fake import FakeExtractor
from test_analysis.extraction.normalize import DraftRow, normalize
from test_analysis.extraction.openrouter import OpenRouterExtractor
from test_analysis.extraction.preprocess import (
    FileTooLarge,
    ScanPages,
    TooManyPages,
    UnsupportedMediaType,
    detect_mime,
    preprocess,
)
from test_analysis.extraction.schema import ExtractedItem, ExtractionResult

__all__ = [
    "DraftRow",
    "ExtractedItem",
    "ExtractionFailed",
    "ExtractionInvalidResponse",
    "ExtractionResult",
    "Extractor",
    "FakeExtractor",
    "FileTooLarge",
    "OpenRouterExtractor",
    "ScanPages",
    "TooManyPages",
    "UnsupportedMediaType",
    "detect_mime",
    "get_extractor",
    "normalize",
    "preprocess",
]
