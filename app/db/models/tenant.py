import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    subdomain = Column(String, unique=True, index=True)
    plan = Column(String, default="free")  # free, pro, enterprise
    status = Column(String, default="active")  # active, suspended, cancelled
    config = Column(JSONB)  # CRM settings, model preferences, etc.
    limits = Column(JSONB)  # API limits, usage limits, etc.
    billing_email = Column(String)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="tenant")
    leads = relationship("Lead", back_populates="tenant")
    agent_executions = relationship("AgentExecution", back_populates="tenant")
    usage_metrics = relationship("UsageMetrics", back_populates="tenant")
    audit_logs = relationship("AuditLog", back_populates="tenant")

    def __repr__(self):
        return f"<Tenant(id={self.id}, name={self.name}, subdomain={self.subdomain})>"