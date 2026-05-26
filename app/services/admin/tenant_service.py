from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models.tenant import Tenant
from app.schemas.tenant import TenantResponse


class TenantService:
    def __init__(self, db: Session):
        self.db = db

    async def get_all_tenants(self, skip: int = 0, limit: int = 50) -> list[TenantResponse]:
        """
        Get all tenants
        """
        tenants = self.db.query(Tenant).offset(skip).limit(limit).all()
        
        return [
            TenantResponse(
                id=str(tenant.id),
                name=tenant.name,
                subdomain=tenant.subdomain,
                plan=tenant.plan,
                status=tenant.status,
                config=tenant.config,
                limits=tenant.limits,
                billing_email=tenant.billing_email,
                is_verified=tenant.is_verified,
                created_at=tenant.created_at,
                updated_at=tenant.updated_at
            )
            for tenant in tenants
        ]

    async def get_tenant(self, tenant_id: str) -> TenantResponse | None:
        """
        Get a specific tenant by ID
        """
        tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
        
        if not tenant:
            return None
            
        return TenantResponse(
            id=str(tenant.id),
            name=tenant.name,
            subdomain=tenant.subdomain,
            plan=tenant.plan,
            status=tenant.status,
            config=tenant.config,
            limits=tenant.limits,
            billing_email=tenant.billing_email,
            is_verified=tenant.is_verified,
            created_at=tenant.created_at,
            updated_at=tenant.updated_at
        )

    async def suspend_tenant(self, tenant_id: str) -> bool:
        """
        Suspend a tenant
        """
        tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
        
        if not tenant:
            return False

        tenant.status = "suspended"
        tenant.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    async def activate_tenant(self, tenant_id: str) -> bool:
        """
        Activate a tenant
        """
        tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
        
        if not tenant:
            return False

        tenant.status = "active"
        tenant.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    async def delete_tenant(self, tenant_id: str) -> bool:
        """
        Delete tenant (soft delete by marking as cancelled)
        """
        tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
        
        if not tenant:
            return False

        tenant.status = "cancelled"
        tenant.updated_at = datetime.utcnow()
        self.db.commit()
        return True