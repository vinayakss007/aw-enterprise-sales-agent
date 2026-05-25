from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # nullable for system actions
    action = Column(String, nullable=False, index=True)  # create, update, delete, login, etc.
    resource_type = Column(String, nullable=False, index=True)  # user, lead, agent, etc.
    resource_id = Column(String, nullable=False, index=True)  # UUID or other identifier
    changes_before = Column(JSONB)  # State before change
    changes_after = Column(JSONB)  # State after change
    ip_address = Column(String, index=True)
    user_agent = Column(Text)
    previous_hash = Column(String(64))  # For tamper resistance
    current_hash = Column(String(64), index=True)  # For tamper resistance

    # Relationships
    tenant = relationship("Tenant", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, resource_type={self.resource_type})>"

# Create composite index for efficient querying
Index('idx_audit_log_tenant_timestamp', AuditLog.tenant_id, AuditLog.timestamp.desc())