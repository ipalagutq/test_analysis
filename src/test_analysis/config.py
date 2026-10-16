"""Application settings read from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration of the service."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    extractor: Literal["openrouter", "fake"] = "fake"
    openrouter_api_key: SecretStr | None = None
    openrouter_model: str | None = None
    database_url: str = "sqlite:///data/patient_card.db"
    upload_dir: str = "data/uploads"
    max_upload_mb: int = Field(default=10, gt=0)
    max_pdf_pages: int = Field(default=5, gt=0)
    llm_timeout_s: float = Field(default=120, gt=0)

    @model_validator(mode="after")
    def require_openrouter_credentials(self) -> "Settings":
        if self.extractor != "openrouter":
            return self
        missing = []
        if not self.openrouter_api_key or not self.openrouter_api_key.get_secret_value():
            missing.append("OPENROUTER_API_KEY")
        if not self.openrouter_model:
            missing.append("OPENROUTER_MODEL")
        if missing:
            raise ValueError(f"EXTRACTOR=openrouter requires env variables: {', '.join(missing)}")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings()
