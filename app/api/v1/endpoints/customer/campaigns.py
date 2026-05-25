
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.campaign import CampaignCreate, CampaignResponse, CampaignUpdate
from app.services.customer.campaign_service import CampaignService

router = APIRouter()

@router.get("/", response_model=list[CampaignResponse])
async def list_campaigns(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List campaigns for the current user's tenant
    """
    campaign_service = CampaignService(db, current_user)
    campaigns = await campaign_service.get_campaigns(skip=skip, limit=limit)
    return campaigns

@router.post("/", response_model=CampaignResponse)
async def create_campaign(
    campaign_in: CampaignCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new campaign
    """
    campaign_service = CampaignService(db, current_user)
    campaign = await campaign_service.create_campaign(campaign_in)
    return campaign

@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get campaign by ID
    """
    campaign_service = CampaignService(db, current_user)
    campaign = await campaign_service.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str,
    campaign_in: CampaignUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update campaign
    """
    campaign_service = CampaignService(db, current_user)
    campaign = await campaign_service.update_campaign(campaign_id, campaign_in)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete campaign
    """
    campaign_service = CampaignService(db, current_user)
    success = await campaign_service.delete_campaign(campaign_id)
    if not success:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"message": "Campaign deleted successfully"}

@router.post("/{campaign_id}/activate")
async def activate_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Activate a campaign
    """
    campaign_service = CampaignService(db, current_user)
    success = await campaign_service.activate_campaign(campaign_id)
    if not success:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"message": "Campaign activated successfully"}

@router.post("/{campaign_id}/deactivate")
async def deactivate_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deactivate a campaign
    """
    campaign_service = CampaignService(db, current_user)
    success = await campaign_service.deactivate_campaign(campaign_id)
    if not success:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"message": "Campaign deactivated successfully"}

@router.post("/{campaign_id}/add-leads")
async def add_leads_to_campaign(
    campaign_id: str,
    lead_ids: list[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add leads to a campaign
    """
    campaign_service = CampaignService(db, current_user)
    result = await campaign_service.add_leads_to_campaign(campaign_id, lead_ids)
    return result