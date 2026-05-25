"""Customer knowledge-base endpoints.

CRUD on ``KnowledgeBase`` rows scoped to the calling user's tenant, plus a
``/lookup`` endpoint that exposes the same retrieval the agent uses (handy
for debugging "why did the agent pick *that* talking point?").
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.knowledge import (
    KnowledgeCreate,
    KnowledgeMatchResponse,
    KnowledgeResponse,
    KnowledgeUpdate,
)
from app.services.admin.audit_service import AuditService
from app.services.customer.knowledge_service import KnowledgeService

router = APIRouter()


def _audit_context(request: Request) -> dict:
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


@router.get("/", response_model=list[KnowledgeResponse])
async def list_entries(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    category: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List knowledge-base entries for the current tenant."""
    return await KnowledgeService(db, current_user).list_entries(
        skip=skip, limit=limit, active_only=active_only, category=category
    )


@router.post("/", response_model=KnowledgeResponse)
async def create_entry(
    payload: KnowledgeCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new knowledge-base entry."""
    entry = await KnowledgeService(db, current_user).create_entry(payload)
    AuditService(db).record(
        tenant_id=str(current_user.tenant_id),
        user_id=str(current_user.id),
        action="knowledge.create",
        resource_type="knowledge",
        resource_id=entry.id,
        changes_after={"title": entry.title, "category": entry.category},
        **_audit_context(request),
    )
    return entry


@router.get("/lookup", response_model=list[KnowledgeMatchResponse])
async def lookup_entries(
    q: str = Query(..., min_length=1, description="Free-text query"),
    limit: int = Query(3, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run the same retrieval the agent uses against the tenant's KB."""
    matches = await KnowledgeService(db, current_user).lookup(
        q, tenant_id=str(current_user.tenant_id), limit=limit
    )
    return [
        KnowledgeMatchResponse(
            id=m.id,
            title=m.title,
            content=m.content,
            category=m.category,
            tags=m.tags,
            score=m.score,
        )
        for m in matches
    ]


@router.get("/{entry_id}", response_model=KnowledgeResponse)
async def get_entry(
    entry_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = await KnowledgeService(db, current_user).get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    return entry


@router.put("/{entry_id}", response_model=KnowledgeResponse)
async def update_entry(
    entry_id: str,
    payload: KnowledgeUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = await KnowledgeService(db, current_user).update_entry(
        entry_id, payload
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    AuditService(db).record(
        tenant_id=str(current_user.tenant_id),
        user_id=str(current_user.id),
        action="knowledge.update",
        resource_type="knowledge",
        resource_id=entry.id,
        changes_after=payload.model_dump(exclude_unset=True),
        **_audit_context(request),
    )
    return entry


@router.delete("/{entry_id}")
async def delete_entry(
    entry_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Soft-delete by flipping ``active`` to false (history is preserved)."""
    success = await KnowledgeService(db, current_user).delete_entry(entry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    AuditService(db).record(
        tenant_id=str(current_user.tenant_id),
        user_id=str(current_user.id),
        action="knowledge.delete",
        resource_type="knowledge",
        resource_id=entry_id,
        **_audit_context(request),
    )
    return {"message": "Knowledge entry archived"}
