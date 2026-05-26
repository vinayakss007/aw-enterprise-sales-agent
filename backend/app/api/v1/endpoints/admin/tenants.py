"""Admin tenant management endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.user import User
from app.api.deps import get_current_admin
from app.services.admin.tenant_service import TenantService

router = APIRouter()


@router.get("/")
async def list_tenants(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    service = TenantService(db)
    tenants = service.get_tenants(skip=skip, limit=limit)
    return {"tenants": [
        {
            "id": str(t.id),
            "name": t.name,
            "subdomain": t.subdomain,
            "plan": t.plan,
            "status": t.status,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tenants
    ]}


@router.post("/{tenant_id}/suspend")
async def suspend_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    service = TenantService(db)
    if not service.suspend_tenant(tenant_id):
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"message": "Tenant suspended"}


@router.post("/{tenant_id}/activate")
async def activate_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    service = TenantService(db)
    if not service.activate_tenant(tenant_id):
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"message": "Tenant activated"}
