"""CRM integration service for customer-facing operations."""
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.db.models.lead import Lead
from app.services.crm import get_crm_adapter, CRMContact
from app.core.exceptions import CRMIntegrationError

logger = logging.getLogger(__name__)


class CRMIntegrationService:
    """Handles CRM sync operations for a tenant."""

    def __init__(self, db: Session, tenant_id: str, crm_provider: str = None, api_key: str = None):
        self.db = db
        self.tenant_id = tenant_id
        self._provider = crm_provider
        self._api_key = api_key

    def _get_adapter(self):
        try:
            return get_crm_adapter(provider=self._provider, api_key=self._api_key)
        except (ValueError, NotImplementedError) as e:
            raise CRMIntegrationError(str(e))

    async def sync_lead_to_crm(self, lead: Lead) -> Optional[str]:
        """
        Sync a lead to the configured CRM.
        Returns the CRM contact ID.
        """
        adapter = self._get_adapter()

        # Check if already synced
        if lead.crm_contact_id:
            # Update existing contact
            updates = {}
            if lead.name:
                parts = lead.name.split(" ", 1)
                updates["first_name"] = parts[0]
                if len(parts) > 1:
                    updates["last_name"] = parts[1]
            if lead.company:
                updates["company"] = lead.company
            if lead.title:
                updates["title"] = lead.title

            try:
                await adapter.update_contact(lead.crm_contact_id, updates)
                return lead.crm_contact_id
            except Exception as e:
                logger.error(f"Failed to update CRM contact {lead.crm_contact_id}: {e}")
                raise CRMIntegrationError(f"Update failed: {e}")

        # Create new contact
        first_name = ""
        last_name = ""
        if lead.name:
            parts = lead.name.split(" ", 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""

        contact = CRMContact(
            id="",
            email=lead.email or "",
            first_name=first_name,
            last_name=last_name,
            company=lead.company or "",
            title=lead.title or "",
            phone=lead.phone or "",
            linkedin_url=lead.linkedin_url or "",
        )

        try:
            created = await adapter.create_contact(contact)
            # Save the CRM ID back to our lead
            lead.crm_contact_id = created.id
            self.db.commit()
            return created.id
        except Exception as e:
            logger.error(f"Failed to create CRM contact for lead {lead.id}: {e}")
            raise CRMIntegrationError(f"Create failed: {e}")

    async def create_note_in_crm(self, contact_id: str, content: str) -> Optional[str]:
        """Create a note in CRM for a contact."""
        adapter = self._get_adapter()
        try:
            note = await adapter.create_note(contact_id, content)
            return note.id
        except Exception as e:
            logger.error(f"Failed to create CRM note: {e}")
            raise CRMIntegrationError(f"Note creation failed: {e}")

    async def search_crm_contact(self, query: str) -> list:
        """Search for contacts in CRM."""
        adapter = self._get_adapter()
        try:
            results = await adapter.search_contacts(query)
            return [
                {
                    "id": c.id,
                    "email": c.email,
                    "name": f"{c.first_name} {c.last_name}".strip(),
                    "company": c.company,
                }
                for c in results
            ]
        except Exception as e:
            logger.error(f"CRM search failed: {e}")
            return []

    async def test_connection(self) -> Dict[str, Any]:
        """Test CRM connection."""
        try:
            adapter = self._get_adapter()
            success = await adapter.test_connection()
            return {"connected": success, "provider": self._provider or "default"}
        except Exception as e:
            return {"connected": False, "error": str(e)}
