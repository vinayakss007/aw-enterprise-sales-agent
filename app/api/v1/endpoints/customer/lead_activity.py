"""Lead activity timeline — unified view of everything that happened to a lead.

Unions:
  * AgentExecution rows (filtered by lead_id)
  * AuditLog rows (filtered by resource_type=lead + resource_id=lead_id)
  * CampaignAssignment step completions

Returns a flat list sorted by timestamp desc so the frontend can render a
simple chronological feed.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.models.agent_execution import AgentExecution
from app.db.models.audit_log import AuditLog
from app.db.models.campaign import CampaignAssignment
from app.db.models.lead import Lead
from app.db.models.user import User

router = APIRouter()


def _agent_events(db: Session, lead_id: str, tenant_id: str) -> list[dict[str, Any]]:
    rows = (
        db.query(AgentExecution)
        .filter(
            AgentExecution.lead_id == lead_id,
            AgentExecution.tenant_id == tenant_id,
        )
        .order_by(AgentExecution.started_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "type": "agent_run",
            "timestamp": row.started_at.isoformat() if row.started_at else row.created_at.isoformat(),
            "summary": f"Agent '{row.agent_type}' run — {'success' if row.success else 'failed'}",
            "details": {
                "agent_type": row.agent_type,
                "success": row.success,
                "tokens_input": row.tokens_input,
                "tokens_output": row.tokens_output,
                "cost_cents": row.cost_cents,
                "execution_id": str(row.id),
            },
        }
        for row in rows
    ]


def _audit_events(db: Session, lead_id: str, tenant_id: str) -> list[dict[str, Any]]:
    rows = (
        db.query(AuditLog)
        .filter(
            AuditLog.tenant_id == tenant_id,
            AuditLog.resource_type == "lead",
            AuditLog.resource_id == lead_id,
        )
        .order_by(AuditLog.timestamp.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "type": "audit",
            "timestamp": row.timestamp.isoformat(),
            "summary": f"{row.action}",
            "details": {
                "action": row.action,
                "changes_after": row.changes_after,
                "user_id": str(row.user_id) if row.user_id else None,
                "ip_address": row.ip_address,
            },
        }
        for row in rows
    ]


def _campaign_events(db: Session, lead_id: str, tenant_id: str) -> list[dict[str, Any]]:
    rows = (
        db.query(CampaignAssignment)
        .filter(CampaignAssignment.lead_id == lead_id)
        .order_by(CampaignAssignment.updated_at.desc())
        .limit(50)
        .all()
    )
    events: list[dict[str, Any]] = []
    for row in rows:
        events.append({
            "type": "campaign",
            "timestamp": (row.updated_at or row.created_at).isoformat(),
            "summary": f"Campaign assignment status: {row.status} (step {row.current_step})",
            "details": {
                "campaign_id": str(row.campaign_id),
                "status": row.status,
                "current_step": row.current_step,
                "completed_steps": row.completed_steps,
            },
        })
    return events


@router.get("/{lead_id}/activity")
async def get_lead_activity(
    lead_id: str,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """Unified activity timeline for a lead."""
    # Verify lead belongs to user's tenant.
    lead = (
        db.query(Lead)
        .filter(Lead.id == lead_id, Lead.tenant_id == current_user.tenant_id)
        .first()
    )
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    tenant_id = str(current_user.tenant_id)
    events: list[dict[str, Any]] = []
    events.extend(_agent_events(db, lead_id, tenant_id))
    events.extend(_audit_events(db, lead_id, tenant_id))
    events.extend(_campaign_events(db, lead_id, tenant_id))

    # Sort by timestamp desc and cap.
    events.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return events[:limit]
