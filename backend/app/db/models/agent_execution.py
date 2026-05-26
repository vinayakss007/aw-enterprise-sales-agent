from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.types import JSONB, UUID
from datetime import datetime
import uuid
from app.db.base import Base


class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False, index=True)
    agent_type = Column(String, nullable=False, index=True)  # research, outreach, follow_up
    trajectory = Column(JSONB, default=list)  # Execution steps and results
    success = Column(Boolean, default=False)
    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    cost_cents = Column(Integer, default=0)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")
    user = relationship("User", back_populates="agent_executions")
    lead = relationship("Lead", back_populates="agent_executions")

    def __repr__(self):
        return f"<AgentExecution(id={self.id}, type={self.agent_type}, success={self.success})>"
