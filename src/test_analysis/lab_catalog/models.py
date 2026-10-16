"""Lab test definitions stored in the catalog."""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, PositiveFloat, model_validator

Sex = Literal["M", "F"]
Flag = Literal["low", "normal", "high", "unknown"]
TestGroup = Literal["cbc", "biochem"]


class ReferenceInterval(BaseModel):
    """Adult reference interval in the canonical unit; an open bound is `None`."""

    model_config = ConfigDict(frozen=True)

    low: float | None = None
    high: float | None = None

    @model_validator(mode="after")
    def require_ordered_bounds(self) -> Self:
        if self.low is None and self.high is None:
            raise ValueError("reference interval needs at least one bound")
        if self.low is not None and self.high is not None and self.low > self.high:
            raise ValueError(f"reference interval low {self.low} > high {self.high}")
        return self


class LabTest(BaseModel):
    """One catalog entry: canonical code, spellings, units and reference intervals."""

    model_config = ConfigDict(frozen=True)

    code: str = Field(pattern=r"^[A-Z0-9]+$")
    name_ru: str = Field(min_length=1)
    group: TestGroup
    synonyms: list[str] = Field(min_length=2)
    unit: str = Field(min_length=1)
    unit_aliases: dict[str, PositiveFloat] = Field(default_factory=dict)
    ref: ReferenceInterval | None = None
    ref_male: ReferenceInterval | None = None
    ref_female: ReferenceInterval | None = None

    @model_validator(mode="after")
    def require_reference_for_both_sexes(self) -> Self:
        if self.ref is None and (self.ref_male is None or self.ref_female is None):
            raise ValueError(f"{self.code}: needs `ref` or both `ref_male` and `ref_female`")
        return self

    def reference_for(self, sex: Sex) -> ReferenceInterval | None:
        """Return the sex-specific interval if present, otherwise the common one."""
        specific = self.ref_male if sex == "M" else self.ref_female
        return specific or self.ref
