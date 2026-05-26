"""Super-admin endpoints — cross-tenant operations.

Only accessible by users with role='superadmin'. These bypass tenant scoping
entirely and give the platform operator full visibility.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_superadmin, get_db
from app.db.models.agent_execution import AgentExecution
from app.db.models.campaign import Campaign
from app.db.models.lead import Lead
from app.db.models.tenant import Tenant
from app.db.models.user import User
from app.services.quota_service import DEFAULT_LIMITS

router = APIRouter()


# --------------------------------------------------------------------------- #
# Schemas
# --------------------------------------------------------------------------- #


class TenantLimitsUpdate(BaseModel):
    max_leads: int | None = None
    max_campaigns: int | None = None
    max_kb_entries: int | None = None
    max_agent_runs_per_day: int | None = None
    max_emails_per_day: int | None = None


class SetUserRoleRequest(BaseModel):
    role: str  # superadmin | owner | admin | user | viewer


# --------------------------------------------------------------------------- #
# Platform overview
# --------------------------------------------------------------------------- #


@router.get("/overview")
async def platform_overview(
    db: Session = Depends(get_db),
    _sa: User = Depends(get_current_superadmin),
) -> dict[str, Any]:
    """System-wide stats for the platform operator."""
    total_tenants = db.query(func.count(Tenant.id)).scalar() or 0
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_leads = db.query(func.count(Lead.id)).scalar() or 0
    total_campaigns = db.query(func.count(Campaign.id)).scalar() or 0
    total_agent_runs = db.query(func.count(AgentExecution.id)).scalar() or 0
    total_cost_cents = (
        db.query(func.sum(AgentExecution.cost_cents)).scalar() or 0
    )
    return {
        "total_tenants": total_tenants,
        "total_users": total_users,
        "total_leads": total_leads,
        "total_campaigns": total_campaigns,
        "total_agent_runs": total_agent_runs,
        "total_cost_usd": round(total_cost_cents / 100, 2),
        "default_limits": DEFAULT_LIMITS,
    }


# --------------------------------------------------------------------------- #
# Cross-tenant user management
# --------------------------------------------------------------------------- #


@router.get("/users")
async def list_all_users(
    skip: int = 0,
    limit: int = Query(100, ge=1, le=500),
    role: str | None = None,
    db: Session = Depends(get_db),
    _sa: User = Depends(get_current_superadmin),
) -> list[dict[str, Any]]:
    """List all users across all tenants. Filterable by role."""
    query = db.query(User).order_by(User.created_at.desc())
    if role:
        query = query.filter(User.role == role)
    users = query.offset(skip).limit(limit).all()
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "name": u.name,
            "role": u.role,
            "is_active": u.is_active,
            "tenant_id": str(u.tenant_id),
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
        }
        for u in users
    ]


@router.put("/users/{user_id}/role")
async def set_user_role(
    user_id: str,
    payload: SetUserRoleRequest,
    db: Session = Depends(get_db),
    _sa: User = Depends(get_current_superadmin),
) -> dict[str, Any]:
    """Change any user's role (including promoting to superadmin)."""
    valid_roles = {"superadmin", "owner", "admin", "user", "viewer"}
    if payload.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Valid: {valid_roles}")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = payload.role
    db.commit()
    return {"user_id": str(user.id), "email": user.email, "role": user.role}


@router.put("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    db: Session = Depends(get_db),
    _sa: User = Depends(get_current_superadmin),
) -> dict[str, str]:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = True
    db.commit()
    return {"message": f"User {user.email} activated"}


@router.put("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    db: Session = Depends(get_db),
    _sa: User = Depends(get_current_superadmin),
) -> dict[str, str]:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    db.commit()
    return {"message": f"User {user.email} deactivated"}


# --------------------------------------------------------------------------- #
# Tenant limits management
# --------------------------------------------------------------------------- #


@router.get("/tenants/{tenant_id}/limits")
async def get_tenant_limits(
    tenant_id: str,
    db: Session = Depends(get_db),
    _sa: User = Depends(get_current_superadmin),
) -> dict[str, Any]:
    """Get the effective limits for a tenant (merged with defaults)."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    effective = {**DEFAULT_LIMITS, **(tenant.limits or {})}
    return {"tenant_id": str(tenant.id), "name": tenant.name, "limits": effective}


@router.put("/tenants/{tenant_id}/limits")
async def set_tenant_limits(
    tenant_id: str,
    payload: TenantLimitsUpdate,
    db: Session = Depends(get_db),
    _sa: User = Depends(get_current_superadmin),
) -> dict[str, Any]:
    """Override resource limits for a specific tenant."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    current = dict(tenant.limits or {})
    update = payload.model_dump(exclude_unset=True)
    current.update(update)
    tenant.limits = current
    db.commit()
    db.refresh(tenant)
    effective = {**DEFAULT_LIMITS, **(tenant.limits or {})}
    return {"tenant_id": str(tenant.id), "name": tenant.name, "limits": effective}


@router.delete("/tenants/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    db: Session = Depends(get_db),
    _sa: User = Depends(get_current_superadmin),
) -> dict[str, str]:
    """Hard-suspend a tenant (sets status=cancelled, deactivates all users)."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    tenant.status = "cancelled"
    # Deactivate all users in the tenant.
    db.query(User).filter(User.tenant_id == tenant_id).update(
        {"is_active": False}, synchronize_session="fetch"
    )
    db.commit()
    return {"message": f"Tenant {tenant.name} cancelled, all users deactivated"}
