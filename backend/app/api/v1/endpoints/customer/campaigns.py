"""Campaign management endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.campaign import CampaignCreate, CampaignUpdate, CampaignResponse
from app.services.customer.campaign_service import CampaignService
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/", response_model=List[CampaignResponse])
async def list_campaigns(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = CampaignService(db, current_user)
    return await service.get_campaigns(skip=skip, limit=limit)


@router.post("/", response_model=CampaignResponse)
async def create_campaign(
    campaign_in: CampaignCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = CampaignService(db, current_user)
    return await service.create_campaign(campaign_in)


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = CampaignService(db, current_user)
    campaign = await service.get_campaign(campaign_id)
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
    service = CampaignService(db, current_user)
    campaign = await service.update_campaign(campaign_id, campaign_in)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = CampaignService(db, current_user)
    if not await service.delete_campaign(campaign_id):
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"message": "Campaign deleted"}


@router.post("/{campaign_id}/activate")
async def activate_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = CampaignService(db, current_user)
    if not await service.activate_campaign(campaign_id):
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"message": "Campaign activated"}


@router.post("/{campaign_id}/deactivate")
async def deactivate_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = CampaignService(db, current_user)
    if not await service.deactivate_campaign(campaign_id):
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"message": "Campaign paused"}


@router.post("/{campaign_id}/add-leads")
async def add_leads_to_campaign(
    campaign_id: str,
    lead_ids: List[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = CampaignService(db, current_user)
    return await service.add_leads_to_campaign(campaign_id, lead_ids)
