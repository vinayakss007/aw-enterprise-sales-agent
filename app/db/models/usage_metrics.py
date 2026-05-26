import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class UsageMetrics(Base):
    __tablename__ = "usage_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    metric_type = Column(String, nullable=False, index=True)
    value = Column(BigInteger, nullable=False, default=1)
    cost_cents = Column(Integer, default=0)
    resource_id = Column(String, nullable=True, index=True)  # UUID or other identifier
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="usage_metrics")

    def __repr__(self):
        return f"<UsageMetrics(id={self.id}, tenant_id={self.tenant_id}, metric_type={self.metric_type}, value={self.value})>"