from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.models.user import User
from app.db.session import get_db

router = APIRouter()

@router.post("/config/{tenant_id}")
async def set_crm_config(
    tenant_id: str,
    config: dict[str, Any],
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Set CRM configuration for a tenant (admin only)
    """
    # This would typically save the configuration to the tenant model
    # In a real implementation, we'd update tenant.config['crm_config'] = config
    return {"success": True, "message": f"CRM configuration updated for tenant {tenant_id}"}

@router.get("/config/{tenant_id}")
async def get_crm_config(
    tenant_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get CRM configuration for a tenant (admin only)
    """
    # This would typically retrieve the configuration from the tenant model
    # In a real implementation, we'd get tenant.config.get('crm_config', {})
    return {"provider": "hubspot", "tenant_id": tenant_id, "config": {}}