import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class UsageMetrics(Base):
    __tablename__ = "usage_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    date = Column(Date, nullable=False, index=True)  # Date for aggregation
    metric_type = Column(String, nullable=False, index=True)  # tokens_in, tokens_out, tasks_completed, etc.
    value = Column(BigInteger, nullable=False)
    cost_cents = Column(Integer, default=0)  # Cost in cents
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="usage_metrics")

    def __repr__(self):
        return f"<UsageMetrics(id={self.id}, tenant_id={self.tenant_id}, metric_type={self.metric_type}, value={self.value})>"