from datetime import datetime
from typing import Any

from pydantic import BaseModel


class TenantBase(BaseModel):
    name: str
    subdomain: str | None = None
    plan: str = "free"
    billing_email: str | None = None

class TenantCreate(TenantBase):
    pass

class TenantUpdate(BaseModel):
    name: str | None = None
    plan: str | None = None
    billing_email: str | None = None
    config: dict[str, Any] | None = None
    limits: dict[str, Any] | None = None

class TenantResponse(TenantBase):
    id: str
    status: str
    config: dict[str, Any] | None = None
    limits: dict[str, Any] | None = None
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True