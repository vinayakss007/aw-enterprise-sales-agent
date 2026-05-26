from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr


class LeadBase(BaseModel):
    email: EmailStr | None = None
    name: str | None = None
    company: str | None = None
    domain: str | None = None
    title: str | None = None
    linkedin_url: str | None = None
    phone: str | None = None
    source: str | None = "agent"

class LeadCreate(LeadBase):
    pass

class LeadUpdate(BaseModel):
    email: EmailStr | None = None
    name: str | None = None
    company: str | None = None
    domain: str | None = None
    title: str | None = None
    linkedin_url: str | None = None
    phone: str | None = None
    status: str | None = None

class LeadResponse(LeadBase):
    id: str
    tenant_id: str
    user_id: str
    status: str
    enriched_data: dict[str, Any] | None = None
    crm_contact_id: str | None = None
    crm_account_id: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True