
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.tenant import TenantResponse
from app.services.admin.tenant_service import TenantService

router = APIRouter()

@router.get("/", response_model=list[TenantResponse])
async def list_tenants(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    List all tenants (admin only)
    """
    tenant_service = TenantService(db)
    tenants = await tenant_service.get_all_tenants(skip=skip, limit=limit)
    return tenants

@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get tenant by ID (admin only)
    """
    tenant_service = TenantService(db)
    tenant = await tenant_service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant

@router.put("/{tenant_id}/suspend")
async def suspend_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Suspend a tenant (admin only)
    """
    tenant_service = TenantService(db)
    success = await tenant_service.suspend_tenant(tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"message": "Tenant suspended successfully"}

@router.put("/{tenant_id}/activate")
async def activate_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Activate a tenant (admin only)
    """
    tenant_service = TenantService(db)
    success = await tenant_service.activate_tenant(tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"message": "Tenant activated successfully"}

@router.delete("/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Delete tenant (admin only) - Soft delete by marking as cancelled
    """
    tenant_service = TenantService(db)
    success = await tenant_service.delete_tenant(tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"message": "Tenant marked for deletion"}