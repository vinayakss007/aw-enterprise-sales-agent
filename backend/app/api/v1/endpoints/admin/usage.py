"""Admin usage metrics endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.user import User
from app.api.deps import get_current_admin
from app.services.admin.usage_service import UsageService

router = APIRouter()


@router.get("/{tenant_id}/summary")
async def get_usage_summary(
    tenant_id: str,
    days: int = 30,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    service = UsageService(db)
    return service.get_usage_summary(tenant_id, days=days)


@router.get("/{tenant_id}/daily")
async def get_daily_usage(
    tenant_id: str,
    days: int = 30,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    service = UsageService(db)
    return {"daily": service.get_daily_usage(tenant_id, days=days)}
