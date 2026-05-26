"""Settings sanity checks."""
from __future__ import annotations


def test_settings_defaults_are_safe():
    from app.core.config import settings

    # Default DB URL must point at localhost — never a real environment.
    assert "localhost" in settings.DATABASE_URL or "127.0.0.1" in settings.DATABASE_URL
    # Driver suffix must match the psycopg3 package shipped in requirements.
    assert settings.DATABASE_URL.startswith("postgresql+psycopg://")


def test_cors_origins_parsed_to_list():
    from app.core.config import Settings

    s = Settings(BACKEND_CORS_ORIGINS="http://a.test, http://b.test , http://c.test")
    assert s.backend_cors_origins_list == [
        "http://a.test",
        "http://b.test",
        "http://c.test",
    ]


def test_cors_origins_empty_string_yields_empty_list():
    from app.core.config import Settings

    s = Settings(BACKEND_CORS_ORIGINS="")
    assert s.backend_cors_origins_list == []
