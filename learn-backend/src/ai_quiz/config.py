"""Environment-backed application configuration."""

from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, AnyHttpUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated settings with safe defaults for local development."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="AI_QUIZ_",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = "AI 知识闯关 API"
    environment: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    api_prefix: str = "/api/v1"
    quiz_run_ttl_seconds: int = Field(default=3600, ge=60, le=86400)

    dashscope_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("DASHSCOPE_API_KEY", "AI_QUIZ_DASHSCOPE_API_KEY"),
    )
    dashscope_base_url: AnyHttpUrl | None = Field(
        default=None,
        validation_alias=AliasChoices("DASHSCOPE_BASE_URL", "AI_QUIZ_DASHSCOPE_BASE_URL"),
    )
    generation_model: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "DASHSCOPE_GENERATION_MODEL",
            "AI_QUIZ_GENERATION_MODEL",
        ),
    )

    def readiness_checks(self) -> dict[str, bool]:
        """Return configuration presence only; never call a paid dependency."""

        return {
            "dashscope_api_key": self.dashscope_api_key is not None,
            "dashscope_base_url": self.dashscope_base_url is not None,
            "generation_model": bool(self.generation_model and self.generation_model.strip()),
        }

    @property
    def is_ready(self) -> bool:
        return all(self.readiness_checks().values())


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load settings once for the process; tests inject settings into the app factory."""

    return Settings()
