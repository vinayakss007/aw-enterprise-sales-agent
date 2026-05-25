from datetime import datetime
from typing import Any

from pydantic import BaseModel


class UsageMetricsResponse(BaseModel):
    date_range: tuple[datetime, datetime]
    granularity: str
    metrics: list[dict[str, Any]]
    totals: dict[str, Any]

class TenantUsageResponse(BaseModel):
    tenant_id: str
    tenant_name: str | None = None
    total_usage: int
    total_cost: float
    active_users: int
    task_count: int

class UsageExportResponse(BaseModel):
    filename: str
    download_url: str
    size: int
    created_at: datetime