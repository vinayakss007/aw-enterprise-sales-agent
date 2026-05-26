
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.lead import LeadCreate, LeadResponse, LeadUpdate
from app.services.customer.lead_service import LeadService

router = APIRouter()

@router.get("/", response_model=list[LeadResponse])
async def list_leads(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List leads for the current user's tenant
    """
    lead_service = LeadService(db, current_user)
    leads = await lead_service.get_leads(skip=skip, limit=limit)
    return leads

@router.post("/", response_model=LeadResponse)
async def create_lead(
    lead_in: LeadCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new lead
    """
    lead_service = LeadService(db, current_user)
    lead = await lead_service.create_lead(lead_in)
    return lead

@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get lead by ID
    """
    lead_service = LeadService(db, current_user)
    lead = await lead_service.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    lead_in: LeadUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update lead
    """
    lead_service = LeadService(db, current_user)
    lead = await lead_service.update_lead(lead_id, lead_in)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@router.delete("/{lead_id}")
async def delete_lead(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete lead (archive)
    """
    lead_service = LeadService(db, current_user)
    success = await lead_service.archive_lead(lead_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"message": "Lead archived successfully"}