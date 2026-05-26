from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.services.customer.crm_integration import CRMIntegrationService
from app.services.customer.lead_service import LeadService

router = APIRouter()

@router.post("/sync/{lead_id}")
async def sync_lead_to_crm(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sync a lead to the configured CRM
    """
    # Get the lead
    lead_service = LeadService(db, current_user)
    lead = await lead_service.get_lead(lead_id)
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Initialize CRM service
    crm_service = CRMIntegrationService(current_user.tenant_id)
    
    # Sync to CRM
    contact_id = await crm_service.sync_lead_to_crm(lead)
    
    if not contact_id:
        raise HTTPException(status_code=500, detail="Failed to sync lead to CRM")
    
    return {
        "success": True,
        "contact_id": contact_id,
        "message": "Lead synced to CRM successfully"
    }

@router.post("/note/{lead_id}")
async def create_crm_note(
    lead_id: str,
    content: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a note in CRM for a lead
    """
    # Get the lead
    lead_service = LeadService(db, current_user)
    lead = await lead_service.get_lead(lead_id)
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Check if contact exists in CRM
    crm_service = CRMIntegrationService(current_user.tenant_id)
    
    # If no contact ID in DB, search by email
    contact_id = lead.crm_contact_id
    if not contact_id:
        contact_info = await crm_service.search_contact_by_email(lead.email)
        if contact_info:
            contact_id = contact_info.get('id')
    
    if not contact_id:
        raise HTTPException(status_code=400, detail="Contact not found in CRM")
    
    # Create note in CRM
    note_id = await crm_service.create_note_in_crm(contact_id, content)
    
    if not note_id:
        raise HTTPException(status_code=500, detail="Failed to create note in CRM")
    
    return {
        "success": True,
        "note_id": note_id,
        "message": "Note created in CRM successfully"
    }