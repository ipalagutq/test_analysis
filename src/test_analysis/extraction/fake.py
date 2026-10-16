"""Deterministic extractor that serves prepared answers without network or API key."""

import hashlib
from pathlib import Path

from test_analysis.extraction.schema import ExtractionResult

FIXTURES_DIR = Path("data/fixtures/extraction")
DEFAULT_FIXTURE = "default.json"


class FakeExtractor:
    """Returns the fixture named by the sha256 of the uploaded file, else `default.json`."""

    def __init__(self, fixtures_dir: Path = FIXTURES_DIR) -> None:
        self._fixtures_dir = fixtures_dir

    @property
    def model_id(self) -> str:
        """Identifier of the model stored with the draft and the visit."""
        return "fake"

    def extract(self, pages: list[bytes], *, source: bytes) -> ExtractionResult:
        """Return the prepared answer for the uploaded file; `pages` are not read."""
        fixture = self._fixtures_dir / f"{hashlib.sha256(source).hexdigest()}.json"
        if not fixture.is_file():
            fixture = self._fixtures_dir / DEFAULT_FIXTURE
        return ExtractionResult.model_validate_json(fixture.read_bytes())
