"""Admin endpoints for the audit log.

Two endpoints:
* ``GET /admin/audit/`` — paginated, filterable list of audit rows for the
  caller's tenant.
* ``GET /admin/audit/verify`` — re-walks the chain and reports whether it's
  intact, plus the IDs of any tampered/missing rows.

Both are tenant-scoped to the calling admin's tenant — even system admins
can never read another tenant's audit log via this endpoint.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db
from app.db.models.user import User
from app.schemas.audit import AuditLogResponse
from app.services.admin.audit_service import AuditService

router = APIRouter()


@router.get("/", response_model=list[AuditLogResponse])
async def list_audit_logs(
    action: str | None = Query(None, description="Filter on the action field"),
    resource_type: str | None = Query(None),
    user_id: str | None = Query(None),
    start_date: str | None = Query(None, description="ISO-8601 lower bound"),
    end_date: str | None = Query(None, description="ISO-8601 upper bound"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> list[AuditLogResponse]:
    """Paginated audit rows for the calling admin's tenant."""
    return await AuditService(db).get_audit_logs(
        tenant_id=str(admin.tenant_id),
        action=action,
        resource_type=resource_type,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )


@router.get("/verify", response_model=dict[str, Any])
async def verify_audit_chain(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> dict[str, Any]:
    """Verify the per-tenant hash chain end-to-end."""
    return AuditService(db).verify_chain(str(admin.tenant_id))
