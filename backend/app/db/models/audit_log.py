from sqlalchemy import Column, String, DateTime, ForeignKey
from app.db.types import JSONB, UUID
from datetime import datetime
import uuid
from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String, nullable=False, index=True)  # create, update, delete, execute
    resource_type = Column(String, nullable=False)  # lead, campaign, agent, user
    resource_id = Column(String)
    details = Column(JSONB, default=dict)
    ip_address = Column(String)
    user_agent = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
