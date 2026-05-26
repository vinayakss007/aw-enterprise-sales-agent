"""Admin endpoint for manually ticking the campaign worker.

Useful for:

* dev/test environments where you don't run the long-lived worker
* operations playbooks ("force a tick after fixing a stuck campaign")

Scoped to the calling admin's tenant so a tenant admin can never fire
another tenant's campaigns.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db
from app.db.models.user import User
from app.workers.campaigns import CampaignWorker

router = APIRouter()


@router.post("/tick", response_model=dict[str, Any])
async def tick_campaign_worker(
    batch_size: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> dict[str, Any]:
    """Process up to ``batch_size`` due assignments for the admin's tenant."""
    worker = CampaignWorker(db)
    stats = await worker.process_due_assignments(
        tenant_id=str(admin.tenant_id), batch_size=batch_size
    )
    return stats.as_dict()
