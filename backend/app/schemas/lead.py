"""Lead schemas."""
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime


class LeadBase(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    company: Optional[str] = None
    domain: Optional[str] = None
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[str] = "manual"


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    company: Optional[str] = None
    domain: Optional[str] = None
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None


class LeadResponse(LeadBase):
    id: str
    tenant_id: str
    user_id: str
    status: str
    enriched_data: Optional[Dict[str, Any]] = None
    crm_contact_id: Optional[str] = None
    crm_account_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
