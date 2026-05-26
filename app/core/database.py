"""Backwards-compatible re-exports.

The canonical homes are ``app.db.base`` (metadata) and ``app.db.session``
(engine / session). This module is kept so that older imports keep working.
"""
from app.db.base import Base
from app.db.session import SessionLocal, engine, get_db

__all__ = ["engine", "SessionLocal", "Base", "get_db"]
