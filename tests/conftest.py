"""Shared pytest fixtures.

Unit tests require nothing beyond the package itself. Integration tests need a
running Postgres reachable via ``TEST_DATABASE_URL``; if that env var is unset
they are skipped, so a fresh checkout can run ``pytest tests/unit`` with no
infrastructure.
"""
from __future__ import annotations

import os
from collections.abc import Generator

import pytest

# Force a non-debug, deterministic config before importing the app.
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("LLM_PROVIDER", "fake")
os.environ.setdefault("EMAIL_PROVIDER", "console")
os.environ.setdefault("SECRET_KEY", "test-secret-key-do-not-use-in-prod")

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


@pytest.fixture(scope="session")
def database_url() -> str:
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL not set; skipping integration tests")
    return TEST_DATABASE_URL


@pytest.fixture(scope="session")
def engine(database_url: str):
    """Create a session-scoped engine pointing at the test database."""
    from sqlalchemy import create_engine

    eng = create_engine(database_url, future=True, pool_pre_ping=True)
    yield eng
    eng.dispose()


@pytest.fixture(scope="session", autouse=False)
def _create_schema(engine):
    """Create all tables once per session against the test DB."""
    from app.db import models  # noqa: F401  (registers all mappers)
    from app.db.base import Base

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture()
def db_session(engine, _create_schema) -> Generator:
    """Per-test session that rolls back at teardown for isolation."""
    from sqlalchemy.orm import sessionmaker

    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection, autoflush=False, autocommit=False, future=True)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session):
    """FastAPI TestClient with the DB session dependency overridden."""
    from fastapi.testclient import TestClient

    from app.api.deps import get_db as deps_get_db
    from app.db.session import get_db as session_get_db
    from app.main import app

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[deps_get_db] = _override_get_db
    app.dependency_overrides[session_get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
