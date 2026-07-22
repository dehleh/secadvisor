"""Application configuration loaded from environment variables."""
from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings sourced from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "CyberCapSec Advisory API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = Field(min_length=32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: str
    TEST_DATABASE_URL: str | None = None

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Anthropic / Claude
    ANTHROPIC_API_KEY: str = ""
    # Haiku 4.5 is ~10–15× cheaper than Opus and strong enough for
    # templated structured-JSON report generation. Override via env to
    # use Sonnet (claude-sonnet-4-5) or Opus (claude-opus-4-7).
    CLAUDE_MODEL: str = "claude-haiku-4-5"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Flutterwave
    FLUTTERWAVE_SECRET_KEY: str = ""
    FLUTTERWAVE_PUBLIC_KEY: str = ""
    FLUTTERWAVE_SECRET_HASH: str = ""
    FLUTTERWAVE_CHECKOUT_CALLBACK_URL: str = "http://localhost:5173/billing/return"

    # Feature flags
    ENABLE_AI_REPORTS: bool = True
    USE_MOCK_AI: bool = False
    USE_MOCK_PAYMENTS: bool = False

    # Internal admin / marketing dashboard. When set, requests carrying
    # `X-Admin-Key: <value>` to /admin/* endpoints are authorised. Leave
    # empty to fully disable the admin surface (the default for prod
    # safety until a key is provisioned via env).
    ADMIN_API_KEY: str = ""

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Allow CORS_ORIGINS to be a JSON string or a list."""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor."""
    return Settings()
