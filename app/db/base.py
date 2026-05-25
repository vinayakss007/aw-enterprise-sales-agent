"""Declarative base + canonical metadata.

All models import ``Base`` from here. The engine and session live in
``app.db.session`` to keep this module free of side effects so that Alembic and
test fixtures can import the metadata without touching the database.
"""
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Project-wide declarative base."""


__all__ = ["Base"]
