from datetime import datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models.audit_log import AuditLog
from app.schemas.audit import AuditLogResponse


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    async def get_audit_logs(
        self,
        tenant_id: str | None = None,
        user_id: str | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 50,
        offset: int = 0
    ) -> list[AuditLogResponse]:
        """
        Get audit logs with filtering options
        """
        query = self.db.query(AuditLog)
        
        # Apply filters
        if tenant_id:
            query = query.filter(AuditLog.tenant_id == tenant_id)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(AuditLog.timestamp >= start_dt)
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(AuditLog.timestamp <= end_dt)
        
        # Order by timestamp descending and apply pagination
        logs = query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()
        
        return [
            AuditLogResponse(
                id=log.id,
                timestamp=log.timestamp,
                tenant_id=str(log.tenant_id),
                user_id=str(log.user_id) if log.user_id else None,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                changes_before=log.changes_before,
                changes_after=log.changes_after,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                previous_hash=log.previous_hash,
                current_hash=log.current_hash
            )
            for log in logs
        ]

    async def get_audit_summary(
        self,
        tenant_id: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None
    ) -> dict[str, Any]:
        """
        Get audit log summary statistics
        """
        query = self.db.query(AuditLog)
        
        # Apply filters
        if tenant_id:
            query = query.filter(AuditLog.tenant_id == tenant_id)
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(AuditLog.timestamp >= start_dt)
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(AuditLog.timestamp <= end_dt)
        
        # Get summary statistics
        total_logs = query.count()
        action_counts = dict(
            self.db.query(AuditLog.action, func.count(AuditLog.id))
            .filter(AuditLog.tenant_id == tenant_id if tenant_id else True)
            .group_by(AuditLog.action)
            .all()
        )
        resource_type_counts = dict(
            self.db.query(AuditLog.resource_type, func.count(AuditLog.id))
            .filter(AuditLog.tenant_id == tenant_id if tenant_id else True)
            .group_by(AuditLog.resource_type)
            .all()
        )
        
        return {
            "total_logs": total_logs,
            "action_counts": action_counts,
            "resource_type_counts": resource_type_counts,
            "date_range": {"start": start_date, "end": end_date}
        }