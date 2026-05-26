"""Customer campaign endpoints + audit hooks for state transitions."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.campaign import CampaignCreate, CampaignResponse, CampaignUpdate
from app.services.admin.audit_service import AuditService
from app.services.customer.campaign_service import CampaignService

router = APIRouter()


def _audit_context(request: Request) -> dict:
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


def _audit(db, user, request, action, resource_id, **after):
    AuditService(db).record(
        tenant_id=str(user.tenant_id),
        user_id=str(user.id),
        action=action,
        resource_type="campaign",
        resource_id=str(resource_id),
        changes_after=after or None,
        **_audit_context(request),
    )


@router.get("/", response_model=list[CampaignResponse])
async def list_campaigns(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List campaigns for the current user's tenant."""
    return await CampaignService(db, current_user).get_campaigns(skip=skip, limit=limit)


@router.post("/", response_model=CampaignResponse)
async def create_campaign(
    campaign_in: CampaignCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new campaign."""
    campaign = await CampaignService(db, current_user).create_campaign(campaign_in)
    _audit(db, current_user, request, "campaign.create", campaign.id, name=campaign.name)
    return campaign


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get campaign by ID."""
    campaign = await CampaignService(db, current_user).get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str,
    campaign_in: CampaignUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update campaign."""
    campaign = await CampaignService(db, current_user).update_campaign(campaign_id, campaign_in)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete campaign (soft)."""
    success = await CampaignService(db, current_user).delete_campaign(campaign_id)
    if not success:
        raise HTTPException(status_code=404, detail="Campaign not found")
    _audit(db, current_user, request, "campaign.delete", campaign_id)
    return {"message": "Campaign deleted successfully"}


@router.post("/{campaign_id}/activate")
async def activate_campaign(
    campaign_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Activate a campaign — recorded in audit."""
    success = await CampaignService(db, current_user).activate_campaign(campaign_id)
    if not success:
        raise HTTPException(status_code=404, detail="Campaign not found")
    _audit(db, current_user, request, "campaign.activate", campaign_id)
    return {"message": "Campaign activated successfully"}


@router.post("/{campaign_id}/deactivate")
async def deactivate_campaign(
    campaign_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deactivate a campaign — recorded in audit."""
    success = await CampaignService(db, current_user).deactivate_campaign(campaign_id)
    if not success:
        raise HTTPException(status_code=404, detail="Campaign not found")
    _audit(db, current_user, request, "campaign.deactivate", campaign_id)
    return {"message": "Campaign deactivated successfully"}


@router.post("/{campaign_id}/add-leads")
async def add_leads_to_campaign(
    campaign_id: str,
    lead_ids: list[str],
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add leads to a campaign."""
    result = await CampaignService(db, current_user).add_leads_to_campaign(
        campaign_id, lead_ids
    )
    _audit(
        db,
        current_user,
        request,
        "campaign.add_leads",
        campaign_id,
        added=result.get("added_leads"),
        requested=result.get("total_requested"),
    )
    return result
