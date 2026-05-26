"""Customer lead endpoints + audit hooks for create/delete + bulk + enrichment."""
from __future__ import annotations

from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    Response,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.lead import Lead
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.lead import LeadCreate, LeadResponse, LeadUpdate
from app.services.admin.audit_service import AuditService
from app.services.customer.enrichment_service import EnrichmentService
from app.services.customer.lead_import import (
    export_leads_csv,
    import_leads_csv,
)
from app.services.customer.lead_scoring import compute_lead_score
from app.services.customer.lead_service import LeadService
from app.services.quota_service import QuotaService
from app.services.usage_writer import record_usage

router = APIRouter()


def _audit_context(request: Request) -> dict[str, Any]:
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


@router.get("/", response_model=list[LeadResponse])
async def list_leads(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List leads for the current user's tenant."""
    return await LeadService(db, current_user).get_leads(skip=skip, limit=limit)


@router.post("/", response_model=LeadResponse)
async def create_lead(
    lead_in: LeadCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new lead."""
    QuotaService(db, current_user).check_lead_create()
    lead = await LeadService(db, current_user).create_lead(lead_in)
    AuditService(db).record(
        tenant_id=str(current_user.tenant_id),
        user_id=str(current_user.id),
        action="lead.create",
        resource_type="lead",
        resource_id=lead.id,
        changes_after={"email": lead.email, "company": lead.company},
        **_audit_context(request),
    )
    record_usage(
        db,
        tenant_id=str(current_user.tenant_id),
        user_id=str(current_user.id),
        metric_type="lead_create",
        commit=False,
    )
    return lead


@router.get("/export.csv")
async def export_leads(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Stream every lead in the tenant as CSV.

    Lives above ``/{lead_id}`` because FastAPI matches in declaration order
    and ``export.csv`` would otherwise be swallowed by the path param.
    """
    leads = (
        db.query(Lead)
        .filter(Lead.tenant_id == current_user.tenant_id)
        .order_by(Lead.created_at.desc())
        .all()
    )
    csv_text = export_leads_csv(leads)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="leads.csv"',
        },
    )


@router.post("/import")
async def import_leads(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Bulk-create / update leads from a CSV upload."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Expected a .csv file")

    raw = await file.read()
    if len(raw) > 10 * 1024 * 1024:  # 10 MB safety cap
        raise HTTPException(status_code=413, detail="CSV exceeds 10MB cap")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400, detail=f"CSV must be UTF-8: {exc}"
        ) from exc

    report = import_leads_csv(db, current_user, text=text)
    AuditService(db).record(
        tenant_id=str(current_user.tenant_id),
        user_id=str(current_user.id),
        action="lead.import",
        resource_type="lead",
        resource_id=file.filename,
        changes_after={
            "created": report.created,
            "updated": report.updated,
            "skipped": report.skipped,
            "error_count": len(report.errors),
        },
        **_audit_context(request),
    )
    return report.as_dict()


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get lead by ID."""
    lead = await LeadService(db, current_user).get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    lead_in: LeadUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update lead."""
    lead = await LeadService(db, current_user).update_lead(lead_id, lead_in)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    AuditService(db).record(
        tenant_id=str(current_user.tenant_id),
        user_id=str(current_user.id),
        action="lead.update",
        resource_type="lead",
        resource_id=lead.id,
        changes_after=lead_in.model_dump(exclude_unset=True),
        **_audit_context(request),
    )
    return lead


@router.delete("/{lead_id}")
async def delete_lead(
    lead_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Archive a lead (soft delete)."""
    success = await LeadService(db, current_user).archive_lead(lead_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lead not found")
    AuditService(db).record(
        tenant_id=str(current_user.tenant_id),
        user_id=str(current_user.id),
        action="lead.archive",
        resource_type="lead",
        resource_id=lead_id,
        **_audit_context(request),
    )
    return {"message": "Lead archived successfully"}


@router.post("/{lead_id}/enrich", response_model=LeadResponse)
async def enrich_lead(
    lead_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run the configured enrichment provider against this lead."""
    service = EnrichmentService(db, current_user)
    lead = await service.enrich_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    AuditService(db).record(
        tenant_id=str(current_user.tenant_id),
        user_id=str(current_user.id),
        action="lead.enrich",
        resource_type="lead",
        resource_id=lead.id,
        changes_after={
            "provider": (lead.enriched_data or {}).get("provider"),
            "confidence": (lead.enriched_data or {}).get("confidence"),
        },
        **_audit_context(request),
    )
    record_usage(
        db,
        tenant_id=str(current_user.tenant_id),
        user_id=str(current_user.id),
        metric_type="enrichment",
        resource_id=lead_id,
        commit=False,
    )
    return await LeadService(db, current_user).get_lead(lead_id)



@router.post("/{lead_id}/score")
async def score_lead(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Compute and store a lead score based on enriched_data."""
    lead = (
        db.query(Lead)
        .filter(Lead.id == lead_id, Lead.tenant_id == current_user.tenant_id)
        .first()
    )
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    score = compute_lead_score(lead.enriched_data)

    # Persist score in enriched_data
    enriched = dict(lead.enriched_data) if lead.enriched_data else {}
    enriched["lead_score"] = score
    lead.enriched_data = enriched
    db.commit()

    return {"lead_id": str(lead.id), "score": score}
