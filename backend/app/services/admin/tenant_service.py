"""Tenant administration service."""
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.models.tenant import Tenant


class TenantService:
    def __init__(self, db: Session):
        self.db = db

    def get_tenants(self, skip: int = 0, limit: int = 50) -> List[Tenant]:
        return self.db.query(Tenant).offset(skip).limit(limit).all()

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        return self.db.query(Tenant).filter(Tenant.id == tenant_id).first()

    def suspend_tenant(self, tenant_id: str) -> bool:
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False
        tenant.status = "suspended"
        tenant.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    def activate_tenant(self, tenant_id: str) -> bool:
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False
        tenant.status = "active"
        tenant.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    def delete_tenant(self, tenant_id: str) -> bool:
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False
        tenant.status = "cancelled"
        tenant.updated_at = datetime.utcnow()
        self.db.commit()
        return True
