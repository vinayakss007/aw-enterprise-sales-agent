"""Per-tenant + per-user resource quota enforcement.

Quotas are stored in ``Tenant.limits`` (JSONB) with the following shape::

    {
        "max_leads": 1000,
        "max_campaigns": 50,
        "max_kb_entries": 200,
        "max_agent_runs_per_day": 100,
        "max_emails_per_day": 500
    }

All limits are optional — an absent key means "unlimited". The platform-wide
defaults are defined in ``DEFAULT_LIMITS`` and can be overridden per tenant.

Usage:

    quota = QuotaService(db, user)
    quota.check_lead_create()        # raises HTTPException(429) if over limit
    quota.check_agent_run()          # same
    quota.check_campaign_create()    # same
    quota.check_email_send()         # same
    quota.check_kb_create()          # same
"""
from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models.agent_execution import AgentExecution
from app.db.models.campaign import Campaign
from app.db.models.knowledge_base import KnowledgeBase
from app.db.models.lead import Lead
from app.db.models.tenant import Tenant
from app.db.models.user import User

# Platform-wide defaults (generous for free tier).
DEFAULT_LIMITS = {
    "max_leads": 5000,
    "max_campaigns": 100,
    "max_kb_entries": 500,
    "max_agent_runs_per_day": 200,
    "max_emails_per_day": 1000,
}


class QuotaService:
    """Check resource usage against tenant limits before writes."""

    def __init__(self, db: Session, user: User) -> None:
        self.db = db
        self.user = user
        self.tenant_id = user.tenant_id
        self._limits: dict | None = None

    @property
    def limits(self) -> dict:
        if self._limits is None:
            tenant = (
                self.db.query(Tenant)
                .filter(Tenant.id == self.tenant_id)
                .first()
            )
            tenant_limits = (tenant.limits or {}) if tenant else {}
            # Merge: tenant overrides take precedence over defaults.
            self._limits = {**DEFAULT_LIMITS, **tenant_limits}
        return self._limits

    def _over(self, resource: str, limit_key: str, current: int) -> None:
        cap = self.limits.get(limit_key)
        if cap is None:
            return  # no limit set = unlimited
        if current >= cap:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Quota exceeded: {resource}. "
                    f"Current: {current}, limit: {cap}. "
                    f"Contact your admin to increase limits."
                ),
            )

    def check_lead_create(self) -> None:
        count = (
            self.db.query(func.count(Lead.id))
            .filter(Lead.tenant_id == self.tenant_id)
            .scalar()
        )
        self._over("leads", "max_leads", count or 0)

    def check_campaign_create(self) -> None:
        count = (
            self.db.query(func.count(Campaign.id))
            .filter(
                Campaign.tenant_id == self.tenant_id,
                Campaign.status != "deleted",
            )
            .scalar()
        )
        self._over("campaigns", "max_campaigns", count or 0)

    def check_kb_create(self) -> None:
        count = (
            self.db.query(func.count(KnowledgeBase.id))
            .filter(
                KnowledgeBase.tenant_id == self.tenant_id,
                KnowledgeBase.active.is_(True),
            )
            .scalar()
        )
        self._over("knowledge_entries", "max_kb_entries", count or 0)

    def check_agent_run(self) -> None:
        since = datetime.utcnow() - timedelta(days=1)
        count = (
            self.db.query(func.count(AgentExecution.id))
            .filter(
                AgentExecution.tenant_id == self.tenant_id,
                AgentExecution.started_at >= since,
            )
            .scalar()
        )
        self._over("agent_runs_today", "max_agent_runs_per_day", count or 0)

    def check_email_send(self) -> None:
        """Approximation: count agent executions of type campaign_email today."""
        since = datetime.utcnow() - timedelta(days=1)
        count = (
            self.db.query(func.count(AgentExecution.id))
            .filter(
                AgentExecution.tenant_id == self.tenant_id,
                AgentExecution.agent_type == "campaign_email",
                AgentExecution.started_at >= since,
            )
            .scalar()
        )
        self._over("emails_today", "max_emails_per_day", count or 0)

    def get_usage_summary(self) -> dict:
        """Return current usage vs limits for dashboard display."""
        since_day = datetime.utcnow() - timedelta(days=1)
        leads = (
            self.db.query(func.count(Lead.id))
            .filter(Lead.tenant_id == self.tenant_id)
            .scalar() or 0
        )
        campaigns = (
            self.db.query(func.count(Campaign.id))
            .filter(Campaign.tenant_id == self.tenant_id, Campaign.status != "deleted")
            .scalar() or 0
        )
        kb_entries = (
            self.db.query(func.count(KnowledgeBase.id))
            .filter(KnowledgeBase.tenant_id == self.tenant_id, KnowledgeBase.active.is_(True))
            .scalar() or 0
        )
        agent_runs_today = (
            self.db.query(func.count(AgentExecution.id))
            .filter(AgentExecution.tenant_id == self.tenant_id, AgentExecution.started_at >= since_day)
            .scalar() or 0
        )
        return {
            "leads": {"current": leads, "limit": self.limits.get("max_leads")},
            "campaigns": {"current": campaigns, "limit": self.limits.get("max_campaigns")},
            "kb_entries": {"current": kb_entries, "limit": self.limits.get("max_kb_entries")},
            "agent_runs_today": {"current": agent_runs_today, "limit": self.limits.get("max_agent_runs_per_day")},
        }


__all__ = ["QuotaService", "DEFAULT_LIMITS"]
