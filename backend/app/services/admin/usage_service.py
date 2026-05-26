"""Usage metrics service."""
from typing import List, Optional, Dict, Any
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import date, timedelta
from app.db.models.usage_metrics import UsageMetrics


class UsageService:
    def __init__(self, db: Session):
        self.db = db

    def get_usage_summary(self, tenant_id: str, days: int = 30) -> Dict[str, Any]:
        """Get aggregated usage for a tenant over the last N days."""
        start_date = date.today() - timedelta(days=days)
        rows = (
            self.db.query(UsageMetrics)
            .filter(
                UsageMetrics.tenant_id == tenant_id,
                UsageMetrics.date >= start_date,
            )
            .all()
        )

        return {
            "tenant_id": tenant_id,
            "period_days": days,
            "total_api_calls": sum(r.api_calls for r in rows),
            "total_agent_executions": sum(r.agent_executions for r in rows),
            "total_tokens_used": sum(r.tokens_used for r in rows),
            "total_leads_created": sum(r.leads_created for r in rows),
            "total_emails_sent": sum(r.emails_sent for r in rows),
            "total_cost_cents": sum(r.cost_cents for r in rows),
        }

    def get_daily_usage(self, tenant_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily usage breakdown."""
        start_date = date.today() - timedelta(days=days)
        rows = (
            self.db.query(UsageMetrics)
            .filter(
                UsageMetrics.tenant_id == tenant_id,
                UsageMetrics.date >= start_date,
            )
            .order_by(UsageMetrics.date.desc())
            .all()
        )
        return [
            {
                "date": str(r.date),
                "api_calls": r.api_calls,
                "agent_executions": r.agent_executions,
                "tokens_used": r.tokens_used,
                "leads_created": r.leads_created,
                "emails_sent": r.emails_sent,
                "cost_cents": r.cost_cents,
            }
            for r in rows
        ]
