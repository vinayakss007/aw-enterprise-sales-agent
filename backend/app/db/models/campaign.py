from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.types import JSONB, UUID
from datetime import datetime
import uuid
from app.db.base import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default="draft")  # draft, active, paused, completed, deleted
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    config = Column(JSONB, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    created_by_user = relationship("User")
    steps = relationship("CampaignStep", back_populates="campaign", cascade="all, delete-orphan",
                         order_by="CampaignStep.order")
    assignments = relationship("CampaignAssignment", back_populates="campaign", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Campaign(id={self.id}, name={self.name}, status={self.status})>"


class CampaignStep(Base):
    __tablename__ = "campaign_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False, index=True)
    order = Column(Integer, nullable=False)
    type = Column(String, nullable=False)  # email, call, task, linkedin
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    delay_days = Column(Integer, default=0)
    subject = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaign = relationship("Campaign", back_populates="steps")


class CampaignAssignment(Base):
    __tablename__ = "campaign_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False, index=True)
    status = Column(String, default="pending")  # pending, active, completed, failed
    current_step = Column(Integer, default=0)
    next_action_date = Column(DateTime)
    completed_steps = Column(JSONB, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaign = relationship("Campaign", back_populates="assignments")
    lead = relationship("Lead")
