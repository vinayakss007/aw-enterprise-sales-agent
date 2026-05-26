"""HubSpot CRM adapter (skeleton).

Implements the ``CRMAdapter`` protocol against the HubSpot CRM v3 API. The
adapter is structured but currently exercises the shape rather than full
fidelity — pagination, retries, rate-limit handling, and the engagements/notes
write-up still need work before this is production-grade.

Auth: HubSpot supports private app tokens (Bearer header) or full OAuth2. We
take a token here for simplicity; an OAuth flow lives one layer up.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings
from app.integrations.crm.base import CRMAdapter, CRMContact, CRMError

logger = logging.getLogger(__name__)


class HubSpotCRMAdapter(CRMAdapter):
    provider = "hubspot"

    def __init__(
        self,
        access_token: str,
        base_url: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not access_token:
            raise CRMError("HubSpot adapter requires an access_token")
        self._token = access_token
        self._base = base_url or settings.HUBSPOT_API_BASE
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(timeout=15.0)

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        url = f"{self._base}{path}"
        try:
            response = await self._client.request(
                method, url, headers=self._headers, **kwargs
            )
        except httpx.HTTPError as exc:  # pragma: no cover — network
            raise CRMError(f"HubSpot transport error: {exc}") from exc
        if response.status_code >= 400:
            raise CRMError(
                f"HubSpot {method} {path} returned {response.status_code}: "
                f"{response.text[:200]}"
            )
        return response

    @staticmethod
    def _to_contact(raw: dict[str, Any]) -> CRMContact:
        props = raw.get("properties") or {}
        first = props.get("firstname") or ""
        last = props.get("lastname") or ""
        full_name = (first + " " + last).strip() or None
        return CRMContact(
            id=str(raw.get("id")),
            email=props.get("email", ""),
            name=full_name,
            company=props.get("company"),
            properties=props,
        )

    async def upsert_contact(
        self,
        *,
        email: str,
        name: str | None = None,
        company: str | None = None,
        properties: dict[str, Any] | None = None,
    ) -> CRMContact:
        existing = await self.search_contact_by_email(email)
        props: dict[str, Any] = {"email": email}
        if name:
            # HubSpot uses firstname/lastname — split naively.
            first, _, last = name.partition(" ")
            props["firstname"] = first
            if last:
                props["lastname"] = last
        if company:
            props["company"] = company
        if properties:
            props.update(properties)
        if existing:
            response = await self._request(
                "PATCH",
                f"/crm/v3/objects/contacts/{existing.id}",
                json={"properties": props},
            )
            return self._to_contact(response.json())
        response = await self._request(
            "POST",
            "/crm/v3/objects/contacts",
            json={"properties": props},
        )
        return self._to_contact(response.json())

    async def get_contact(self, contact_id: str) -> CRMContact | None:
        try:
            response = await self._request(
                "GET",
                f"/crm/v3/objects/contacts/{contact_id}",
                params={"properties": "email,firstname,lastname,company"},
            )
        except CRMError:
            return None
        return self._to_contact(response.json())

    async def search_contact_by_email(self, email: str) -> CRMContact | None:
        payload = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "propertyName": "email",
                            "operator": "EQ",
                            "value": email,
                        }
                    ]
                }
            ],
            "properties": ["email", "firstname", "lastname", "company"],
            "limit": 1,
        }
        response = await self._request(
            "POST", "/crm/v3/objects/contacts/search", json=payload
        )
        results = response.json().get("results") or []
        return self._to_contact(results[0]) if results else None

    async def create_note(self, contact_id: str, content: str) -> str:
        # HubSpot models notes as engagement objects associated with contacts.
        # The minimal viable shape:
        payload = {
            "properties": {
                "hs_note_body": content,
                "hs_timestamp": "0",  # API sets to "now" when missing/zero
            },
            "associations": [
                {
                    "to": {"id": contact_id},
                    "types": [
                        {
                            "associationCategory": "HUBSPOT_DEFINED",
                            # 202 = note → contact association id in HubSpot.
                            "associationTypeId": 202,
                        }
                    ],
                }
            ],
        }
        response = await self._request(
            "POST", "/crm/v3/objects/notes", json=payload
        )
        body = response.json()
        return str(body.get("id", ""))

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()


__all__ = ["HubSpotCRMAdapter"]
