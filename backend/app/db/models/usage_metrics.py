from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey
from datetime import datetime, date
import uuid
from app.db.base import Base
from app.db.types import UUID


class UsageMetrics(Base):
    __tablename__ = "usage_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    date = Column(Date, default=date.today, index=True)
    api_calls = Column(Integer, default=0)
    agent_executions = Column(Integer, default=0)
    tokens_used = Column(Integer, default=0)
    leads_created = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)
    cost_cents = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
