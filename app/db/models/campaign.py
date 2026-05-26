import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default="draft")  # draft, active, paused, completed, deleted
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    config = Column(JSONB)  # Additional campaign configuration
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    created_by_user = relationship("User")
    steps = relationship("CampaignStep", back_populates="campaign", cascade="all, delete-orphan")
    assignments = relationship("CampaignAssignment", back_populates="campaign", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Campaign(id={self.id}, name={self.name}, status={self.status})>"

class CampaignStep(Base):
    __tablename__ = "campaign_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False, index=True)
    order = Column(Integer, nullable=False)  # Step order in the campaign
    type = Column(String, nullable=False)  # email, call, task, etc.
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)  # Main content of the step
    delay_days = Column(Integer, default=0)  # Days to wait before this step
    subject = Column(String)  # Email subject if this is an email step
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaign = relationship("Campaign", back_populates="steps")

    def __repr__(self):
        return f"<CampaignStep(id={self.id}, campaign_id={self.campaign_id}, order={self.order})>"

class CampaignAssignment(Base):
    __tablename__ = "campaign_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False, index=True)
    status = Column(String, default="pending")  # pending, active, completed, failed
    next_action_date = Column(DateTime)  # When to execute the next step
    current_step = Column(Integer, default=0)  # Current step index
    completed_steps = Column(JSONB, default=list)  # List of completed step IDs
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaign = relationship("Campaign", back_populates="assignments")
    lead = relationship("Lead")

    def __repr__(self):
        return f"<CampaignAssignment(id={self.id}, campaign_id={self.campaign_id}, lead_id={self.lead_id}, status={self.status})>"