"""Lead management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.lead import LeadCreate, LeadUpdate, LeadResponse
from app.services.customer.lead_service import LeadService
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/")
async def list_leads(
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    status: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = LeadService(db, current_user)
    leads = await service.get_leads(
        skip=skip, limit=limit, status=status,
        search=search, sort_by=sort_by, sort_order=sort_order,
    )
    total = await service.get_lead_count(status=status)
    return {"leads": leads, "total": total}


@router.post("/", response_model=LeadResponse)
async def create_lead(
    lead_in: LeadCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = LeadService(db, current_user)
    return await service.create_lead(lead_in)


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = LeadService(db, current_user)
    lead = await service.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    lead_in: LeadUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = LeadService(db, current_user)
    lead = await service.update_lead(lead_id, lead_in)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.delete("/{lead_id}")
async def archive_lead(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = LeadService(db, current_user)
    if not await service.archive_lead(lead_id):
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"message": "Lead archived"}
