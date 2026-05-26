"""Lightweight usage-metrics writer.

Call ``record_usage(...)`` after every billable action to populate the
``usage_metrics`` table that the admin dashboard reads from. This is a
thin wrapper — no batching, no async queue — because the volume per
request is exactly 1 row and we're already inside a DB transaction.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models.usage_metrics import UsageMetrics


def record_usage(
    db: Session,
    *,
    tenant_id: str,
    user_id: str | None = None,
    metric_type: str,
    value: int = 1,
    cost_cents: int = 0,
    resource_id: str | None = None,
    commit: bool = True,
) -> UsageMetrics:
    """Write a single usage metric row. Call after each billable action.

    metric_type examples:
      - "agent_run"
      - "campaign_email"
      - "lead_create"
      - "enrichment"
      - "csv_import"
    """
    row = UsageMetrics(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=user_id,
        timestamp=datetime.utcnow(),
        metric_type=metric_type,
        value=value,
        cost_cents=cost_cents,
        resource_id=resource_id,
    )
    db.add(row)
    if commit:
        db.commit()
    return row


__all__ = ["record_usage"]
