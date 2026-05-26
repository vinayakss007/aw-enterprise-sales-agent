"""HubSpot CRM adapter - real implementation using HubSpot API v3."""
import logging
from typing import Optional, Dict, Any, List
import httpx
from app.services.crm.base import CRMAdapter, CRMContact, CRMNote, CRMDeal

logger = logging.getLogger(__name__)

HUBSPOT_API_BASE = "https://api.hubapi.com"


class HubSpotAdapter(CRMAdapter):
    """HubSpot CRM adapter using their REST API v3."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=HUBSPOT_API_BASE,
            headers=self.headers,
            timeout=30.0,
        )

    async def create_contact(self, contact: CRMContact) -> CRMContact:
        properties = {
            "email": contact.email,
            "firstname": contact.first_name,
            "lastname": contact.last_name,
            "company": contact.company,
            "jobtitle": contact.title,
            "phone": contact.phone,
        }
        if contact.linkedin_url:
            properties["hs_linkedinid"] = contact.linkedin_url

        async with self._client() as client:
            response = await client.post(
                "/crm/v3/objects/contacts",
                json={"properties": properties},
            )
            response.raise_for_status()
            data = response.json()

        props = data.get("properties", {})
        return CRMContact(
            id=data["id"],
            email=props.get("email", contact.email),
            first_name=props.get("firstname", ""),
            last_name=props.get("lastname", ""),
            company=props.get("company", ""),
            title=props.get("jobtitle", ""),
            phone=props.get("phone", ""),
            properties=props,
        )

    async def get_contact(self, contact_id: str) -> Optional[CRMContact]:
        async with self._client() as client:
            response = await client.get(f"/crm/v3/objects/contacts/{contact_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()

        props = data.get("properties", {})
        return CRMContact(
            id=data["id"],
            email=props.get("email", ""),
            first_name=props.get("firstname", ""),
            last_name=props.get("lastname", ""),
            company=props.get("company", ""),
            title=props.get("jobtitle", ""),
            phone=props.get("phone", ""),
            properties=props,
        )

    async def update_contact(self, contact_id: str, updates: Dict[str, Any]) -> CRMContact:
        # Map our field names to HubSpot property names
        field_map = {
            "first_name": "firstname",
            "last_name": "lastname",
            "email": "email",
            "company": "company",
            "title": "jobtitle",
            "phone": "phone",
            "linkedin_url": "hs_linkedinid",
        }
        properties = {}
        for key, value in updates.items():
            hs_key = field_map.get(key, key)
            properties[hs_key] = value

        async with self._client() as client:
            response = await client.patch(
                f"/crm/v3/objects/contacts/{contact_id}",
                json={"properties": properties},
            )
            response.raise_for_status()
            data = response.json()

        props = data.get("properties", {})
        return CRMContact(
            id=data["id"],
            email=props.get("email", ""),
            first_name=props.get("firstname", ""),
            last_name=props.get("lastname", ""),
            company=props.get("company", ""),
            title=props.get("jobtitle", ""),
            phone=props.get("phone", ""),
            properties=props,
        )

    async def search_contacts(self, query: str) -> List[CRMContact]:
        search_body = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "propertyName": "email",
                            "operator": "CONTAINS_TOKEN",
                            "value": query,
                        }
                    ]
                }
            ],
            "limit": 20,
        }

        async with self._client() as client:
            response = await client.post(
                "/crm/v3/objects/contacts/search",
                json=search_body,
            )
            response.raise_for_status()
            data = response.json()

        contacts = []
        for result in data.get("results", []):
            props = result.get("properties", {})
            contacts.append(CRMContact(
                id=result["id"],
                email=props.get("email", ""),
                first_name=props.get("firstname", ""),
                last_name=props.get("lastname", ""),
                company=props.get("company", ""),
                title=props.get("jobtitle", ""),
                phone=props.get("phone", ""),
                properties=props,
            ))
        return contacts

    async def create_note(self, contact_id: str, content: str, note_type: str = "note") -> CRMNote:
        # Create a note engagement
        payload = {
            "properties": {
                "hs_timestamp": "",
                "hs_note_body": content,
            },
            "associations": [
                {
                    "to": {"id": contact_id},
                    "types": [
                        {"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 202}
                    ],
                }
            ],
        }

        async with self._client() as client:
            response = await client.post(
                "/crm/v3/objects/notes",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        return CRMNote(
            id=data["id"],
            contact_id=contact_id,
            content=content,
            note_type=note_type,
            created_at=data.get("createdAt", ""),
        )

    async def get_notes(self, contact_id: str) -> List[CRMNote]:
        async with self._client() as client:
            response = await client.get(
                f"/crm/v3/objects/contacts/{contact_id}/associations/notes"
            )
            if response.status_code == 404:
                return []
            response.raise_for_status()
            data = response.json()

        notes = []
        for result in data.get("results", []):
            notes.append(CRMNote(
                id=result.get("id", ""),
                contact_id=contact_id,
                content="",  # Would need a separate fetch for body
                note_type="note",
            ))
        return notes

    async def create_deal(self, deal: CRMDeal) -> CRMDeal:
        properties = {
            "dealname": deal.title,
            "amount": str(deal.amount_cents / 100),
            "dealstage": deal.stage,
        }
        properties.update(deal.properties)

        payload = {
            "properties": properties,
            "associations": [
                {
                    "to": {"id": deal.contact_id},
                    "types": [
                        {"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 3}
                    ],
                }
            ],
        }

        async with self._client() as client:
            response = await client.post(
                "/crm/v3/objects/deals",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        return CRMDeal(
            id=data["id"],
            contact_id=deal.contact_id,
            title=deal.title,
            amount_cents=deal.amount_cents,
            stage=deal.stage,
            properties=data.get("properties", {}),
        )

    async def test_connection(self) -> bool:
        try:
            async with self._client() as client:
                response = await client.get("/crm/v3/objects/contacts?limit=1")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"HubSpot connection test failed: {e}")
            return False
