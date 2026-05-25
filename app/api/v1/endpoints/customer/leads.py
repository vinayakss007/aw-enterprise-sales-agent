"""Customer lead endpoints + audit hooks for create/delete."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.lead import LeadCreate, LeadResponse, LeadUpdate
from app.services.admin.audit_service import AuditService
from app.services.customer.lead_service import LeadService

router = APIRouter()


def _audit_context(request: Request) -> dict:
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


@router.get("/", response_model=list[LeadResponse])
async def list_leads(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List leads for the current user's tenant."""
    return await LeadService(db, current_user).get_leads(skip=skip, limit=limit)


@router.post("/", response_model=LeadResponse)
async def create_lead(
    lead_in: LeadCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new lead."""
    lead = await LeadService(db, current_user).create_lead(lead_in)
    AuditService(db).record(
        tenant_id=str(current_user.tenant_id),
        user_id=str(current_user.id),
        action="lead.create",
        resource_type="lead",
        resource_id=lead.id,
        changes_after={"email": lead.email, "company": lead.company},
        **_audit_context(request),
    )
    return lead


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get lead by ID."""
    lead = await LeadService(db, current_user).get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    lead_in: LeadUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update lead."""
    lead = await LeadService(db, current_user).update_lead(lead_id, lead_in)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    AuditService(db).record(
        tenant_id=str(current_user.tenant_id),
        user_id=str(current_user.id),
        action="lead.update",
        resource_type="lead",
        resource_id=lead.id,
        changes_after=lead_in.model_dump(exclude_unset=True),
        **_audit_context(request),
    )
    return lead


@router.delete("/{lead_id}")
async def delete_lead(
    lead_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Archive a lead (soft delete)."""
    success = await LeadService(db, current_user).archive_lead(lead_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lead not found")
    AuditService(db).record(
        tenant_id=str(current_user.tenant_id),
        user_id=str(current_user.id),
        action="lead.archive",
        resource_type="lead",
        resource_id=lead_id,
        **_audit_context(request),
    )
    return {"message": "Lead archived successfully"}
