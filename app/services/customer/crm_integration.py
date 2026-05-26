"""Customer-facing CRM integration service.

Thin orchestration layer over a per-tenant ``CRMAdapter`` (see
``app.integrations.crm``). The endpoint code only ever talks to this service,
so swapping CRM providers is a tenant-config change, not a code change.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.db.models.lead import Lead
from app.db.models.tenant import Tenant
from app.integrations.crm.base import CRMAdapter, CRMError
from app.integrations.crm.factory import get_crm_adapter

logger = logging.getLogger(__name__)


def _tenant_config(db: Session | None, tenant_id: str) -> dict[str, Any] | None:
    if db is None:
        return None
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    return tenant.config if tenant and tenant.config else None


class CRMIntegrationService:
    def __init__(
        self,
        tenant_id: str,
        *,
        db: Session | None = None,
        adapter: CRMAdapter | None = None,
    ) -> None:
        self.tenant_id = str(tenant_id)
        self._db = db
        self._adapter: CRMAdapter | None = adapter

    @property
    def adapter(self) -> CRMAdapter:
        if self._adapter is None:
            self._adapter = get_crm_adapter(_tenant_config(self._db, self.tenant_id))
        return self._adapter

    async def sync_lead_to_crm(self, lead: Lead) -> str | None:
        if not lead.email:
            logger.info("Skipping CRM sync for lead %s (no email)", lead.id)
            return None
        try:
            contact = await self.adapter.upsert_contact(
                email=lead.email,
                name=lead.name,
                company=lead.company,
                properties={"linkedin_url": lead.linkedin_url} if lead.linkedin_url else None,
            )
        except CRMError as exc:
            logger.warning("CRM upsert failed for lead %s: %s", lead.id, exc)
            return None
        return contact.id

    async def create_note_in_crm(self, contact_id: str, content: str) -> str | None:
        try:
            return await self.adapter.create_note(contact_id, content)
        except CRMError as exc:
            logger.warning("CRM note create failed for %s: %s", contact_id, exc)
            return None

    async def get_contact_from_crm(self, contact_id: str) -> dict[str, Any] | None:
        try:
            contact = await self.adapter.get_contact(contact_id)
        except CRMError as exc:
            logger.warning("CRM get_contact failed for %s: %s", contact_id, exc)
            return None
        if contact is None:
            return None
        return {
            "id": contact.id,
            "email": contact.email,
            "name": contact.name,
            "company": contact.company,
            "properties": contact.properties,
        }

    async def search_contact_by_email(self, email: str) -> dict[str, Any] | None:
        try:
            contact = await self.adapter.search_contact_by_email(email)
        except CRMError as exc:
            logger.warning("CRM search failed for %s: %s", email, exc)
            return None
        if contact is None:
            return None
        return {
            "id": contact.id,
            "email": contact.email,
            "name": contact.name,
            "company": contact.company,
            "found": True,
        }

    async def close(self) -> None:
        if self._adapter is not None:
            await self._adapter.close()
