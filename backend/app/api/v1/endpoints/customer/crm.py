"""CRM integration endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.lead import Lead
from app.services.customer.crm_integration import CRMIntegrationService
from app.api.deps import get_current_user
from app.core.exceptions import CRMIntegrationError

router = APIRouter()


@router.post("/sync-lead/{lead_id}")
async def sync_lead_to_crm(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Sync a lead to the configured CRM."""
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.tenant_id == current_user.tenant_id,
    ).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    service = CRMIntegrationService(db, str(current_user.tenant_id))
    try:
        contact_id = await service.sync_lead_to_crm(lead)
        return {"crm_contact_id": contact_id, "status": "synced"}
    except CRMIntegrationError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/search")
async def search_crm(
    query: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Search the CRM for contacts."""
    service = CRMIntegrationService(db, str(current_user.tenant_id))
    results = await service.search_crm_contact(query)
    return {"results": results}


@router.get("/test-connection")
async def test_crm_connection(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Test CRM connection."""
    service = CRMIntegrationService(db, str(current_user.tenant_id))
    return await service.test_connection()
