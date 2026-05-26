"""SQLAlchemy engine and session factory.

The engine is created lazily so module import never fails when ``DATABASE_URL``
points at an unreachable host (e.g. during unit testing or local dev without
Postgres running).
"""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def _build_engine() -> Engine:
    return create_engine(
        settings.DATABASE_URL,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_POOL_OVERFLOW,
        pool_pre_ping=True,
        echo=settings.DEBUG,
        future=True,
    )


engine: Engine = _build_engine()
SessionLocal: sessionmaker[Session] = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, future=True
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


__all__ = ["engine", "SessionLocal", "get_db"]
