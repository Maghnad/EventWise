"""Application settings loaded from environment variables.

Uses ``pydantic-settings`` to validate and parse ``.env`` at import time.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the EventWise application."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Database ────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/eventwise"

    # ── OpenAI / GenAI ─────────────────────────────────
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # ── Auth / JWT ─────────────────────────────────────
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 15

    # ── App ────────────────────────────────────────────
    app_env: str = "development"
    app_debug: bool = True
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    from pydantic import field_validator, model_validator

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            import json
            v_stripped = v.strip()
            if v_stripped.startswith("[") and v_stripped.endswith("]"):
                try:
                    parsed = json.loads(v_stripped)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed]
                except json.JSONDecodeError:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @model_validator(mode="after")
    def validate_production_security(self) -> Settings:
        """Fail fast in production if security configurations are insecure."""
        if self.app_env.lower() in ("production", "prod"):
            if self.jwt_secret in ("change-me", "secret", "default", "") or len(self.jwt_secret) < 32:
                raise ValueError(
                    "FATAL SECURITY CONFIGURATION: In production mode, JWT_SECRET must be at least "
                    "32 characters long and cannot use default/weak placeholders."
                )
            if "*" in self.cors_origins:
                raise ValueError(
                    "FATAL SECURITY CONFIGURATION: CORS origins cannot contain wildcard '*' in production."
                )
        return self


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance (singleton)."""
    return Settings()

