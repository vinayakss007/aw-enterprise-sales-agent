from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.db.types import JSONB, UUID
from datetime import datetime
import uuid
from app.db.base import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    subdomain = Column(String, unique=True, index=True)
    plan = Column(String, default="free")  # free, pro, enterprise
    status = Column(String, default="active")  # active, suspended, cancelled
    config = Column(JSONB, default=dict)  # CRM settings, preferences
    limits = Column(JSONB, default=dict)  # Usage limits
    billing_email = Column(String)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="tenant")

    def __repr__(self):
        return f"<Tenant(id={self.id}, name={self.name})>"
