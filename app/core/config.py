"""Application settings.

All secrets and environment-specific values are sourced from environment
variables or a local ``.env`` file. Defaults here are safe for local
development only — never put real credentials in this file.
"""
from __future__ import annotations

import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ---- App ----
    PROJECT_NAME: str = "Enterprise Sales Agent"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # ---- Database ----
    # Default points at a local Postgres so a fresh checkout never accidentally
    # connects to a real environment. The ``+psycopg`` driver suffix matches the
    # psycopg3 package shipped in requirements.txt.
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/sales_agent",
    )
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "20"))
    DATABASE_POOL_OVERFLOW: int = int(os.getenv("DATABASE_POOL_OVERFLOW", "10"))

    # ---- JWT ----
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ---- LLM ----
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    PRIMARY_MODEL: str = os.getenv("PRIMARY_MODEL", "gpt-4o-mini")
    FALLBACK_MODEL: str = os.getenv("FALLBACK_MODEL", "gpt-4o")
    # ``fake`` runs an offline deterministic agent (used in tests + when no key
    # is set). ``openai`` activates the real client.
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "fake")

    # ---- Enrichment / search ----
    SERPAPI_API_KEY: str = os.getenv("SERPAPI_API_KEY", "")
    CLEARBIT_API_KEY: str = os.getenv("CLEARBIT_API_KEY", "")

    # ---- Redis ----
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # ---- Security ----
    BACKEND_CORS_ORIGINS: str = os.getenv(
        "BACKEND_CORS_ORIGINS",
        "http://localhost,http://localhost:3000,http://localhost:8000",
    )

    # ---- Rate limiting ----
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

    # ---- Tenancy ----
    MULTI_TENANCY: bool = os.getenv("MULTI_TENANCY", "true").lower() == "true"

    # ---- Observability ----
    OTEL_EXPORTER_OTLP_ENDPOINT: str = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    # Tracing imports a lot of optional dependencies; keep it off by default and
    # let deployments opt in.
    TRACING_ENABLED: bool = os.getenv("TRACING_ENABLED", "false").lower() == "true"

    # ---- File storage ----
    FILE_STORAGE_PATH: str = os.getenv("FILE_STORAGE_PATH", "./uploads")

    # ---- Email ----
    EMAIL_PROVIDER: str = os.getenv("EMAIL_PROVIDER", "console")  # console | smtp
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "noreply@example.com")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    # ---- OAuth ----
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "")

    # ---- SSO ----
    SSO_SAML_METADATA_URL: str | None = os.getenv("SSO_SAML_METADATA_URL")

    # ---- CRM ----
    DEFAULT_CRM_PROVIDER: str = os.getenv("DEFAULT_CRM_PROVIDER", "mock")
    HUBSPOT_API_BASE: str = os.getenv("HUBSPOT_API_BASE", "https://api.hubapi.com")

    # Pydantic v2 / pydantic-settings v2 config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def backend_cors_origins_list(self) -> list[str]:
        if isinstance(self.BACKEND_CORS_ORIGINS, str):
            return [
                origin.strip()
                for origin in self.BACKEND_CORS_ORIGINS.split(",")
                if origin.strip()
            ]
        return list(self.BACKEND_CORS_ORIGINS)


settings = Settings()
