from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.types import JSONB, UUID
from datetime import datetime
import uuid
from app.db.base import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    email = Column(String, index=True)
    name = Column(String)
    company = Column(String, index=True)
    domain = Column(String, index=True)
    title = Column(String)
    linkedin_url = Column(String)
    phone = Column(String)
    status = Column(String, default="new")  # new, contacted, qualified, closed, archived
    source = Column(String, default="manual")  # manual, import, agent, crm_sync
    enriched_data = Column(JSONB, default=dict)
    crm_contact_id = Column(String)
    crm_account_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    created_by_user = relationship("User", back_populates="leads")
    agent_executions = relationship("AgentExecution", back_populates="lead")

    def __repr__(self):
        return f"<Lead(id={self.id}, name={self.name}, company={self.company})>"
