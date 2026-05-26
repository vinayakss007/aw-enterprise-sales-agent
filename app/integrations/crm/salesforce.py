"""Salesforce CRM adapter (skeleton).

Implements ``CRMAdapter`` against the Salesforce REST API. Salesforce auth
is more involved than HubSpot:

  * **Username + password + security token** (legacy SOAP login) — works for
    sandboxes and CLI use, but each org needs the security token reset by
    its admin and the flow is being phased out.
  * **OAuth2 client credentials** (server-to-server) — recommended for
    production. Requires a connected app + client_id + client_secret.

This skeleton accepts a pre-fetched ``access_token`` + ``instance_url``
pair so the CRMAdapter contract is honored regardless of how those were
obtained. The OAuth flow itself lives one layer up (and isn't part of this
PR — needs your Salesforce sandbox).

API surface implemented:
  * upsert_contact     → /services/data/vXX.X/sobjects/Contact (composite
                          upsert by Email)
  * search_contact     → /services/data/vXX.X/parameterizedSearch (SOSL)
  * get_contact        → /services/data/vXX.X/sobjects/Contact/{Id}
  * create_note        → /services/data/vXX.X/sobjects/Note
                          (associated to the contact via ParentId)

Pagination, retries, and the bulk API are deliberately out of scope for v1;
add when the first real Salesforce tenant lands.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.integrations.crm.base import CRMAdapter, CRMContact, CRMError

logger = logging.getLogger(__name__)

DEFAULT_API_VERSION = "v60.0"


class SalesforceCRMAdapter(CRMAdapter):
    provider = "salesforce"

    def __init__(
        self,
        access_token: str,
        instance_url: str,
        *,
        api_version: str = DEFAULT_API_VERSION,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not access_token:
            raise CRMError("SalesforceCRMAdapter requires an access_token")
        if not instance_url:
            raise CRMError("SalesforceCRMAdapter requires an instance_url")
        self._token = access_token
        # Salesforce gives us back a per-org base URL — strip a trailing
        # slash so we can compose paths cleanly.
        self._base = instance_url.rstrip("/")
        self._api_version = api_version
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(timeout=15.0)

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    @property
    def _api_root(self) -> str:
        return f"/services/data/{self._api_version}"

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        url = f"{self._base}{path}"
        try:
            response = await self._client.request(
                method, url, headers=self._headers, **kwargs
            )
        except httpx.HTTPError as exc:  # pragma: no cover — network
            raise CRMError(f"Salesforce transport error: {exc}") from exc
        if response.status_code >= 400:
            raise CRMError(
                f"Salesforce {method} {path} returned {response.status_code}: "
                f"{response.text[:200]}"
            )
        return response

    @staticmethod
    def _to_contact(record: dict[str, Any]) -> CRMContact:
        # Salesforce returns ``Id``, ``FirstName``, ``LastName``, ``Email``,
        # ``AccountId`` etc. Account name lives one hop away on
        # ``Account.Name`` — only present when the SOQL query asked for it.
        first = record.get("FirstName") or ""
        last = record.get("LastName") or ""
        full_name = (first + " " + last).strip() or None
        company = None
        account = record.get("Account")
        if isinstance(account, dict):
            company = account.get("Name")
        return CRMContact(
            id=str(record.get("Id") or record.get("id")),
            email=record.get("Email", ""),
            name=full_name,
            company=company,
            properties={k: v for k, v in record.items() if v is not None},
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
        # Salesforce expects FirstName / LastName as separate fields and
        # a non-null LastName is required on Contact creation.
        body: dict[str, Any] = {"Email": email}
        if name:
            first, _, last = name.partition(" ")
            body["FirstName"] = first
            body["LastName"] = last or first or "Unknown"
        elif not existing:
            body["LastName"] = "Unknown"
        if company:
            # Company on a Contact is exposed via the linked Account; for
            # the skeleton we just write it as a custom property and leave
            # the proper Account upsert to a follow-up.
            body["Description"] = body.get("Description") or f"Company: {company}"
        if properties:
            body.update(properties)

        if existing:
            await self._request(
                "PATCH",
                f"{self._api_root}/sobjects/Contact/{existing.id}",
                json=body,
            )
            return await self.get_contact(existing.id) or existing

        response = await self._request(
            "POST",
            f"{self._api_root}/sobjects/Contact",
            json=body,
        )
        result = response.json()
        contact_id = str(result.get("id"))
        return CRMContact(
            id=contact_id,
            email=email,
            name=name,
            company=company,
            properties=body,
        )

    async def get_contact(self, contact_id: str) -> CRMContact | None:
        try:
            response = await self._request(
                "GET",
                f"{self._api_root}/sobjects/Contact/{contact_id}",
            )
        except CRMError:
            return None
        return self._to_contact(response.json())

    async def search_contact_by_email(self, email: str) -> CRMContact | None:
        # SOQL via parameterizedSearch keeps the API simple and avoids
        # building string concat queries that could be SOQL-injectable.
        payload = {
            "q": email,
            "sobjects": [
                {
                    "name": "Contact",
                    "fields": ["Id", "FirstName", "LastName", "Email", "AccountId"],
                    "where": f"Email = {self._escape(email)}",
                }
            ],
        }
        response = await self._request(
            "POST",
            f"{self._api_root}/parameterizedSearch",
            json=payload,
        )
        records = (
            response.json().get("searchRecords")
            or response.json().get("records")
            or []
        )
        if not records:
            return None
        return self._to_contact(records[0])

    @staticmethod
    def _escape(value: str) -> str:
        # SOQL string literals are wrapped in single quotes; escape backslashes
        # and single quotes within. Defensive — parameterizedSearch already
        # handles this for us when ``q`` is set, but the explicit ``where``
        # clause is interpolated.
        escaped = value.replace("\\", "\\\\").replace("'", "\\'")
        return f"'{escaped}'"

    async def create_note(self, contact_id: str, content: str) -> str:
        # Note (legacy) is the simplest associated record. ContentNote is
        # newer but requires a FileVersion + ContentDocumentLink chain that
        # adds three round-trips for marginal benefit.
        payload = {
            "Title": "Sales agent note",
            "Body": content,
            "ParentId": contact_id,
            "IsPrivate": False,
        }
        response = await self._request(
            "POST",
            f"{self._api_root}/sobjects/Note",
            json=payload,
        )
        return str(response.json().get("id", ""))

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()


__all__ = ["SalesforceCRMAdapter"]
