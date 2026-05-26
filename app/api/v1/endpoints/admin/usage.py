
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.usage import TenantUsageResponse, UsageMetricsResponse
from app.services.admin.usage_service import UsageService

router = APIRouter()

@router.get("/", response_model=list[TenantUsageResponse])
async def get_tenant_usage(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    limit: int = Query(50, le=1000),
    offset: int = Query(0),
    sort_by: str = Query("usage", regex="^(usage|cost|users|tasks)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get tenant usage metrics with pagination (admin only)
    """
    usage_service = UsageService(db)
    return await usage_service.get_tenant_usage(start_date, end_date, limit, offset, sort_by, sort_order)

@router.get("/export")
async def export_usage_report(
    start_date: str,
    end_date: str,
    report_type: str = Query("csv", regex="^(csv|excel|pdf)$"),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Export usage data in different formats (admin only)
    """
    usage_service = UsageService(db)
    return await usage_service.export_report(start_date, end_date, report_type)

@router.get("/metrics", response_model=UsageMetricsResponse)
async def get_system_usage(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    granularity: str = Query("day", regex="^(hour|day|week|month)$"),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get system-wide usage metrics (admin only)
    """
    usage_service = UsageService(db)
    return await usage_service.get_system_metrics(start_date, end_date, granularity)