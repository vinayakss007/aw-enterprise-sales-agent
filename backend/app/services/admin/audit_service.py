"""Audit logging service."""
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.models.audit_log import AuditLog


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def log_action(
        self,
        tenant_id: str,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str = None,
        details: Dict[str, Any] = None,
        ip_address: str = None,
        user_agent: str = None,
    ) -> None:
        """Record an audit log entry."""
        entry = AuditLog(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(entry)
        self.db.commit()

    def get_logs(
        self,
        tenant_id: str,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve audit logs with optional filtering."""
        query = self.db.query(AuditLog).filter(AuditLog.tenant_id == tenant_id)

        if action:
            query = query.filter(AuditLog.action == action)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)

        logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()

        return [
            {
                "id": str(log.id),
                "user_id": str(log.user_id),
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "details": log.details,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]
