"""Choice of the extractor implementation from settings."""

from test_analysis.config import Settings
from test_analysis.extraction.base import Extractor
from test_analysis.extraction.fake import FakeExtractor
from test_analysis.extraction.openrouter import OpenRouterExtractor


def get_extractor(settings: Settings) -> Extractor:
    """Return the extractor selected by `EXTRACTOR`."""
    if settings.extractor == "fake":
        return FakeExtractor()
    # Settings validation guarantees both values when EXTRACTOR=openrouter
    assert settings.openrouter_api_key is not None and settings.openrouter_model
    return OpenRouterExtractor(
        api_key=settings.openrouter_api_key,
        model=settings.openrouter_model,
        timeout_s=settings.llm_timeout_s,
    )
