from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
<<<<<<< HEAD
    app_name: str = "AI Job Fit Analyzer API"
    environment: str = Field(default="development", alias="ENV")
    llm_provider: str = Field(default="auto", alias="LLM_PROVIDER")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-5.5", alias="OPENAI_MODEL")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-3.5-flash", alias="GEMINI_MODEL")
    gemini_response_schema_enabled: bool = Field(default=False, alias="GEMINI_RESPONSE_SCHEMA_ENABLED")
=======
    app_name: str = "CV Fit Analyst Agent API"
    environment: str = Field(default="development", alias="ENV")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-3.5-flash", alias="GEMINI_MODEL")
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
    app_api_key: str | None = Field(default=None, alias="APP_API_KEY")
    allowed_origins: str = Field(default="*", alias="ALLOWED_ORIGINS")
    request_timeout_seconds: float = Field(default=60.0, alias="REQUEST_TIMEOUT_SECONDS")
    max_input_chars: int = Field(default=45000, alias="MAX_INPUT_CHARS")
    max_source_chars: int = Field(default=70000, alias="MAX_SOURCE_CHARS")
    rate_limit_per_minute: int = Field(default=30, alias="RATE_LIMIT_PER_MINUTE")
    public_demo_enabled: bool = Field(default=False, alias="PUBLIC_DEMO_ENABLED")
    public_demo_daily_limit: int = Field(default=10, alias="PUBLIC_DEMO_DAILY_LIMIT")
    demo_max_input_chars: int = Field(default=12000, alias="DEMO_MAX_INPUT_CHARS")
<<<<<<< HEAD
    local_analysis_fallback_enabled: bool = Field(default=True, alias="LOCAL_ANALYSIS_FALLBACK_ENABLED")
    job_browser_crawler_enabled: bool = Field(default=False, alias="JOB_BROWSER_CRAWLER_ENABLED")
    job_browser_timeout_seconds: float = Field(default=18.0, alias="JOB_BROWSER_TIMEOUT_SECONDS")
    topcv_enable_edge_crawler: bool = Field(default=False, alias="TOPCV_ENABLE_EDGE_CRAWLER")
    topcv_edge_path: str | None = Field(default=None, alias="TOPCV_EDGE_PATH")
    topcv_edge_headless: bool = Field(default=True, alias="TOPCV_EDGE_HEADLESS")
    topcv_browser_timeout_seconds: float = Field(default=18.0, alias="TOPCV_BROWSER_TIMEOUT_SECONDS")
=======
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        origins = [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]
        return origins or ["*"]

<<<<<<< HEAD
    @property
    def active_llm_provider(self) -> str:
        provider = self.llm_provider.strip().lower()
        if provider in {"openai", "gemini"}:
            return provider
        if self.openai_api_key:
            return "openai"
        if self.gemini_api_key:
            return "gemini"
        return "openai"

    @property
    def has_llm_credentials(self) -> bool:
        if self.active_llm_provider == "gemini":
            return bool(self.gemini_api_key)
        return bool(self.openai_api_key)

=======
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144

@lru_cache
def get_settings() -> Settings:
    return Settings()
