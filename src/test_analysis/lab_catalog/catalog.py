"""Lab test catalog: name matching, unit conversion and reference flags."""

import re
from functools import lru_cache
from pathlib import Path
from typing import Self

from pydantic import BaseModel, Field, PrivateAttr, model_validator

from test_analysis.lab_catalog.models import Flag, LabTest, Sex

CATALOG_PATH = Path("data/lab_catalog.json")

_NAME_NOISE = re.compile(r"[\s.()\-]+")
_CYRILLIC_TO_LATIN = str.maketrans(
    {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh",
        "з": "z", "и": "i", "й": "i", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
        "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "c",
        "ч": "h", "ш": "sh", "щ": "sh", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu",
        "я": "ya",
    }
)  # fmt: skip


def normalize_name(name: str) -> str:
    """Reduce a test name to its matching key: lowercase, `ё→е`, no spaces/dots/brackets/hyphens."""
    return _NAME_NOISE.sub("", name.lower().replace("ё", "е"))


def normalize_unit(unit: str) -> str:
    """Reduce a unit to a script-independent key, so `мкмоль/л` equals `µmol/L`."""
    key = "".join(unit.lower().split())
    for micro in ("µ", "μ", "мк", "mc"):
        key = key.replace(micro, "u")
    key = key.replace("×", "").replace("*", "^")
    return key.translate(_CYRILLIC_TO_LATIN)


class LabCatalog(BaseModel):
    """Validated set of lab tests with lookup by spelling and unit."""

    tests: list[LabTest] = Field(min_length=30, max_length=50)

    _test_by_code: dict[str, LabTest] = PrivateAttr(default_factory=dict)
    _code_by_name: dict[str, str] = PrivateAttr(default_factory=dict)
    _factor_by_unit: dict[str, dict[str, float]] = PrivateAttr(default_factory=dict)

    @model_validator(mode="after")
    def require_unique_spellings(self) -> Self:
        codes: set[str] = set()
        code_by_name: dict[str, str] = {}
        for test in self.tests:
            if test.code in codes:
                raise ValueError(f"duplicate code {test.code}")
            codes.add(test.code)
            for spelling in (test.code, test.name_ru, *test.synonyms):
                key = normalize_name(spelling)
                owner = code_by_name.setdefault(key, test.code)
                if owner != test.code:
                    raise ValueError(f"synonym {spelling!r} is shared by {owner} and {test.code}")
        return self

    @model_validator(mode="after")
    def require_consistent_unit_factors(self) -> Self:
        for test in self.tests:
            factor_by_unit = {normalize_unit(test.unit): 1.0}
            for alias, factor in test.unit_aliases.items():
                known = factor_by_unit.setdefault(normalize_unit(alias), factor)
                if known != factor:
                    raise ValueError(f"{test.code}: unit {alias!r} has conflicting factors")
        return self

    def model_post_init(self, context: object) -> None:
        for test in self.tests:
            self._test_by_code[test.code] = test
            for spelling in (test.code, test.name_ru, *test.synonyms):
                self._code_by_name[normalize_name(spelling)] = test.code
            factor_by_unit = {normalize_unit(test.unit): 1.0}
            for alias, factor in test.unit_aliases.items():
                factor_by_unit[normalize_unit(alias)] = factor
            self._factor_by_unit[test.code] = factor_by_unit

    def find(self, code: str) -> LabTest | None:
        """Return the catalog entry for a canonical code."""
        return self._test_by_code.get(code)

    def match(self, name_raw: str) -> str | None:
        """Return the canonical code for a test name as printed on the scan."""
        return self._code_by_name.get(normalize_name(name_raw))

    def convert(self, code: str, value: float, unit: str | None) -> tuple[float, str] | None:
        """Convert a value to the canonical unit; `None` for an unknown code or unit."""
        test = self.find(code)
        if test is None or unit is None:
            return None
        factor = self._factor_by_unit[code].get(normalize_unit(unit))
        if factor is None:
            return None
        return value * factor, test.unit

    def compute_flag(self, code: str, value: float, sex: Sex) -> Flag:
        """Compare a canonical value with the adult reference interval for the sex."""
        test = self.find(code)
        interval = test.reference_for(sex) if test else None
        if interval is None:
            return "unknown"
        if interval.low is not None and value < interval.low:
            return "low"
        if interval.high is not None and value > interval.high:
            return "high"
        return "normal"


def load_catalog(path: Path) -> LabCatalog:
    """Read and validate a catalog JSON file."""
    return LabCatalog.model_validate_json(path.read_bytes())


@lru_cache
def get_catalog() -> LabCatalog:
    """Return the process-wide catalog loaded from `data/lab_catalog.json`."""
    return load_catalog(CATALOG_PATH)


def match(name_raw: str) -> str | None:
    """Return the canonical code for a test name as printed on the scan."""
    return get_catalog().match(name_raw)


def convert(code: str, value: float, unit: str | None) -> tuple[float, str] | None:
    """Convert a value to the canonical unit; `None` for an unknown code or unit."""
    return get_catalog().convert(code, value, unit)


def compute_flag(code: str, value: float, sex: Sex) -> Flag:
    """Compare a canonical value with the adult reference interval for the sex."""
    return get_catalog().compute_flag(code, value, sex)
