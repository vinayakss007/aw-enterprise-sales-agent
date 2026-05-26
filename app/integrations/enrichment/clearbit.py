"""Clearbit enrichment provider (skeleton).

Implements the ``EnrichmentProvider`` contract against the Clearbit
Enrichment API. Auth uses HTTP basic with the API key as username and
empty password.
"""
from __future__ import annotations

import logging

import httpx

from app.integrations.enrichment.base import (
    EnrichmentError,
    EnrichmentProvider,
    LeadFacts,
)

logger = logging.getLogger(__name__)


class ClearbitEnrichmentProvider(EnrichmentProvider):
    provider = "clearbit"

    def __init__(
        self,
        api_key: str,
        company_url: str = "https://company.clearbit.com/v2/companies/find",
        combined_url: str = "https://person.clearbit.com/v2/combined/find",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not api_key:
            raise EnrichmentError("ClearbitEnrichmentProvider requires an api_key")
        self._api_key = api_key
        self._company_url = company_url
        self._combined_url = combined_url
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(timeout=15.0)

    @property
    def _auth(self) -> tuple[str, str]:
        return (self._api_key, "")

    async def enrich_by_domain(self, domain: str) -> LeadFacts:
        if not domain:
            return LeadFacts(provider=self.provider, confidence=0.0)
        try:
            response = await self._client.get(
                self._company_url,
                params={"domain": domain},
                auth=self._auth,
            )
        except httpx.HTTPError as exc:  # pragma: no cover - network defensive
            raise EnrichmentError(f"Clearbit transport error: {exc}") from exc
        if response.status_code == 404:
            return LeadFacts(provider=self.provider, confidence=0.0)
        if response.status_code >= 400:
            raise EnrichmentError(
                f"Clearbit /companies/find returned {response.status_code}: "
                f"{response.text[:200]}"
            )
        return self._parse_company(response.json())

    async def enrich_by_email(self, email: str) -> LeadFacts:
        if not email:
            return LeadFacts(provider=self.provider, confidence=0.0)
        try:
            response = await self._client.get(
                self._combined_url,
                params={"email": email},
                auth=self._auth,
            )
        except httpx.HTTPError as exc:  # pragma: no cover - network defensive
            raise EnrichmentError(f"Clearbit transport error: {exc}") from exc
        if response.status_code == 404:
            return LeadFacts(provider=self.provider, confidence=0.0)
        if response.status_code >= 400:
            raise EnrichmentError(
                f"Clearbit /combined/find returned {response.status_code}: "
                f"{response.text[:200]}"
            )
        body = response.json() or {}
        return self._parse_company(body.get("company") or {})

    @staticmethod
    def _parse_company(payload: dict) -> LeadFacts:
        if not payload:
            return LeadFacts(provider="clearbit", confidence=0.0)
        category = payload.get("category") or {}
        metrics = payload.get("metrics") or {}
        site = payload.get("site") or {}
        geo = payload.get("geo") or {}
        city = geo.get("city")
        country = geo.get("country") or ""
        headquarters = (
            f"{city}, {country}".strip(", ") if city else None
        )
        return LeadFacts(
            company=payload.get("name"),
            industry=category.get("industry"),
            employee_count=metrics.get("employees"),
            annual_revenue=metrics.get("annualRevenue"),
            description=payload.get("description") or site.get("description"),
            headquarters=headquarters,
            website=payload.get("domain") and f"https://{payload['domain']}",
            linkedin_url=(payload.get("linkedin") or {}).get("handle"),
            twitter_handle=(payload.get("twitter") or {}).get("handle"),
            technologies=list(payload.get("tech") or []),
            tags=list(payload.get("tags") or []),
            extra={"clearbit_id": payload.get("id")} if payload.get("id") else {},
            provider="clearbit",
            confidence=0.9,
        )

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()


__all__ = ["ClearbitEnrichmentProvider"]
