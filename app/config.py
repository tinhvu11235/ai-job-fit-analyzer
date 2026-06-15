from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CV Fit Analyst Agent API"
    environment: str = Field(default="development", alias="ENV")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-3.5-flash", alias="GEMINI_MODEL")
    app_api_key: str | None = Field(default=None, alias="APP_API_KEY")
    allowed_origins: str = Field(default="*", alias="ALLOWED_ORIGINS")
    request_timeout_seconds: float = Field(default=60.0, alias="REQUEST_TIMEOUT_SECONDS")
    max_input_chars: int = Field(default=45000, alias="MAX_INPUT_CHARS")
    max_source_chars: int = Field(default=70000, alias="MAX_SOURCE_CHARS")
    rate_limit_per_minute: int = Field(default=30, alias="RATE_LIMIT_PER_MINUTE")
    public_demo_enabled: bool = Field(default=False, alias="PUBLIC_DEMO_ENABLED")
    public_demo_daily_limit: int = Field(default=10, alias="PUBLIC_DEMO_DAILY_LIMIT")
    demo_max_input_chars: int = Field(default=12000, alias="DEMO_MAX_INPUT_CHARS")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        origins = [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]
        return origins or ["*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
