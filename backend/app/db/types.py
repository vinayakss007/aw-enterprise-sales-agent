"""Custom SQLAlchemy types for cross-database compatibility."""
import uuid as uuid_mod
from sqlalchemy import JSON, String
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB, UUID as PG_UUID
from sqlalchemy.types import TypeDecorator


class JSONB(TypeDecorator):
    """
    JSONB type that works with PostgreSQL (real JSONB) and SQLite (JSON fallback).
    """
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_JSONB())
        return dialect.type_descriptor(JSON())


class UUID(TypeDecorator):
    """
    UUID type that works with PostgreSQL (native UUID) and SQLite (String(36)).
    """
    impl = String(36)
    cache_ok = True

    def __init__(self, as_uuid=True, **kwargs):
        self.as_uuid = as_uuid
        super().__init__(**kwargs)

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=self.as_uuid))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        if isinstance(value, uuid_mod.UUID):
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if self.as_uuid and not isinstance(value, uuid_mod.UUID):
            return uuid_mod.UUID(value)
        return value
