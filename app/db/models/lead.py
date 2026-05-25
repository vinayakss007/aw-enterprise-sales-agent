import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    email = Column(String, index=True)
    name = Column(String)
    company = Column(String, index=True)
    domain = Column(String, index=True)
    title = Column(String)
    linkedin_url = Column(String)
    phone = Column(String)
    status = Column(String, default="new")  # new, contacted, qualified, closed
    source = Column(String, default="agent")  # agent, import, form, etc.
    enriched_data = Column(JSONB)
    crm_contact_id = Column(String)  # ID in external CRM
    crm_account_id = Column(String)  # ID in external CRM
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="leads")
    created_by_user = relationship("User", back_populates="leads")
    agent_executions = relationship("AgentExecution", back_populates="lead")

    def __repr__(self):
        return f"<Lead(id={self.id}, name={self.name}, company={self.company}, tenant_id={self.tenant_id})>"