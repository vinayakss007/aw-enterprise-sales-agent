"""Shared test fixtures."""
import uuid
import os
import pytest
from datetime import datetime
from unittest.mock import MagicMock
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from app.db.base import Base
from app.db.models import *  # noqa: register all models
from app.db.models.tenant import Tenant
from app.db.models.user import User
from app.db.models.lead import Lead
from app.core.security import get_password_hash


# Use SQLite for tests (fast, no external deps)
TEST_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture(scope="session")
def engine():
    """Create test database engine."""
    # Remove stale test db
    if os.path.exists("./test.db"):
        os.remove("./test.db")
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})

    # Enable foreign key support in SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test.db"):
        os.remove("./test.db")


@pytest.fixture
def db_session(engine):
    """Create a test database session that rolls back after each test."""
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def tenant(db_session: Session) -> Tenant:
    """Create a test tenant with unique subdomain."""
    t = Tenant(
        id=uuid.uuid4(),
        name="Test Corp",
        subdomain=f"test-corp-{uuid.uuid4().hex[:8]}",
        plan="pro",
        status="active",
    )
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)
    return t


@pytest.fixture
def user(db_session: Session, tenant: Tenant) -> User:
    """Create a test user."""
    u = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email=f"test-{uuid.uuid4().hex[:8]}@testcorp.com",
        name="Test User",
        hashed_password=get_password_hash("testpass123"),
        role="owner",
        is_active=True,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


@pytest.fixture
def lead(db_session: Session, tenant: Tenant, user: User) -> Lead:
    """Create a test lead."""
    lead = Lead(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        user_id=user.id,
        email="john@acme.com",
        name="John Smith",
        company="Acme Corp",
        domain="acme.com",
        title="VP of Sales",
        status="new",
        source="manual",
    )
    db_session.add(lead)
    db_session.commit()
    db_session.refresh(lead)
    return lead
