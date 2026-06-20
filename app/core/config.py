"""
Centralized configuration via Pydantic Settings.

Loads from environment variables and the .env file at project root.
Use get_settings() to access the cached singleton.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── LLM provider ─────────────────────────────────────────
    default_provider: str = "google"
    llm_temperature: float = 0.6
    llm_max_tokens: int = 4096
    llm_timeout: int = 300
    ollama_api_base: str = "http://127.0.0.1:11434"
    ollama_model: str = "nemotron-3-ultra:cloud"

    # ── API Keys ─────────────────────────────────────────────
    gemini_api_key: str | None = None
    serp_api_key: str | None = None
    nvidia_api_key: str | None = None

    # ── Auth & Payments ──────────────────────────────────────
    jwt_secret: str = "super-secret-jwt-key-replace-in-production"
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_price_basic: str | None = None
    stripe_price_pro: str | None = None
    stripe_price_max: str | None = None

    # ── LinkedIn OAuth ────────────────────────────────────────
    linkedin_client_id: str = ""
    linkedin_client_secret: str = ""
    linkedin_redirect_uri: str = "http://localhost:8000/callback"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
