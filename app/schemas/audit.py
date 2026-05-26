from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditLogBase(BaseModel):
    tenant_id: str
    user_id: str | None = None
    action: str
    resource_type: str
    resource_id: str
    changes_before: dict[str, Any] | None = None
    changes_after: dict[str, Any] | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    previous_hash: str | None = None
    current_hash: str | None = None

class AuditLogCreate(AuditLogBase):
    pass

class AuditLogResponse(AuditLogBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class AuditLogSummary(BaseModel):
    total_logs: int
    action_counts: dict[str, int]
    resource_type_counts: dict[str, int]
    date_range: dict[str, str]