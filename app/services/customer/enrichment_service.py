"""Lead enrichment service.

Wraps an ``EnrichmentProvider`` and merges its output into
``Lead.enriched_data``. We never blindly overwrite existing facts: a new
provider's payload is only persisted when the new ``confidence`` matches
or exceeds the previous one. This lets a tenant call enrichment several
times (Fake -> Clearbit upgrade) without losing real data.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.db.models.lead import Lead
from app.db.models.tenant import Tenant
from app.db.models.user import User
from app.integrations.enrichment.base import (
    EnrichmentError,
    EnrichmentProvider,
    LeadFacts,
)
from app.integrations.enrichment.factory import get_enrichment_provider

logger = logging.getLogger(__name__)


def _tenant_config(db: Session, tenant_id: str) -> dict[str, Any] | None:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    return tenant.config if tenant and tenant.config else None


def _confidence(payload: dict[str, Any] | None) -> float:
    if not payload:
        return 0.0
    try:
        return float(payload.get("confidence", 0.0))
    except (TypeError, ValueError):
        return 0.0


class EnrichmentService:
    """Service-level wrapper used by the lead endpoints."""

    def __init__(
        self,
        db: Session,
        user: User,
        *,
        provider: EnrichmentProvider | None = None,
    ) -> None:
        self.db = db
        self.user = user
        self.tenant_id = str(user.tenant_id)
        self._provider_override = provider

    @property
    def provider(self) -> EnrichmentProvider:
        if self._provider_override is not None:
            return self._provider_override
        self._provider_override = get_enrichment_provider(
            _tenant_config(self.db, self.tenant_id)
        )
        return self._provider_override

    async def enrich_lead(self, lead_id: str) -> Lead | None:
        """Enrich a single lead by id and persist the result.

        Returns the refreshed ``Lead``, or ``None`` if the lead doesn't
        belong to the caller's tenant. Raises ``EnrichmentError`` only on
        unrecoverable provider errors — empty results are persisted as
        confidence=0 and the lead is returned untouched.
        """
        lead = (
            self.db.query(Lead)
            .filter(Lead.id == lead_id, Lead.tenant_id == self.tenant_id)
            .first()
        )
        if not lead:
            return None

        facts = await self._lookup(lead)
        new_payload = facts.to_dict()
        new_payload["enriched_at"] = datetime.utcnow().isoformat()

        existing = lead.enriched_data or {}
        if _confidence(new_payload) < _confidence(existing):
            logger.info(
                "enrichment.skip lead=%s prev_confidence=%.2f new=%.2f",
                lead_id,
                _confidence(existing),
                _confidence(new_payload),
            )
            return lead

        # Merge: scalar fields from new override existing nulls; lists union.
        merged = dict(existing)
        for key, value in new_payload.items():
            if value is None:
                continue
            if isinstance(value, list) and isinstance(merged.get(key), list):
                merged[key] = sorted(set(merged[key]) | set(value))
            else:
                merged[key] = value

        # Surface a few headline fields directly on the Lead row when
        # they're missing — saves the UI from always reading
        # ``enriched_data`` for table rendering.
        if facts.company and not lead.company:
            lead.company = facts.company
        if facts.linkedin_url and not lead.linkedin_url:
            lead.linkedin_url = facts.linkedin_url
        if facts.website and not lead.domain:
            # Strip protocol + path so domain stays clean.
            domain = facts.website.split("://", 1)[-1].split("/", 1)[0]
            lead.domain = domain or lead.domain

        lead.enriched_data = merged
        lead.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(lead)
        return lead

    async def _lookup(self, lead: Lead) -> LeadFacts:
        try:
            if lead.domain:
                facts = await self.provider.enrich_by_domain(lead.domain)
                if facts.confidence > 0:
                    return facts
            if lead.email:
                return await self.provider.enrich_by_email(lead.email)
            return LeadFacts(provider=self.provider.provider, confidence=0.0)
        except EnrichmentError as exc:
            logger.warning("Enrichment failed for lead %s: %s", lead.id, exc)
            raise

    async def close(self) -> None:
        if self._provider_override is not None:
            await self._provider_override.close()


__all__ = ["EnrichmentService"]
