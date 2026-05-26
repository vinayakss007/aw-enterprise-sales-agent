"""Deterministic offline enrichment provider.

Used in tests and as the default in dev environments where no real
enrichment account is configured. Derives plausible-looking facts from
the input domain so downstream code (and tests) can exercise the full
flow without a network call.
"""
from __future__ import annotations

import hashlib

from app.integrations.enrichment.base import EnrichmentProvider, LeadFacts

_INDUSTRIES = (
    "Software",
    "Financial Services",
    "Healthcare",
    "Manufacturing",
    "Retail",
    "Media",
    "Logistics",
    "Education",
    "Consulting",
    "Energy",
)

_SIZE_BUCKETS = (
    (10, 100_000),
    (50, 500_000),
    (200, 5_000_000),
    (1_000, 50_000_000),
    (5_000, 500_000_000),
)


class FakeEnrichmentProvider(EnrichmentProvider):
    provider = "fake"

    async def enrich_by_domain(self, domain: str) -> LeadFacts:
        # Hash the domain so repeat lookups always produce the same result.
        domain_clean = (domain or "").lower().strip()
        for prefix in ("https://", "http://", "www."):
            if domain_clean.startswith(prefix):
                domain_clean = domain_clean[len(prefix):]
        if not domain_clean:
            return LeadFacts(provider=self.provider, confidence=0.0)

        h = hashlib.sha256(domain_clean.encode("utf-8")).digest()
        industry = _INDUSTRIES[h[0] % len(_INDUSTRIES)]
        bucket = _SIZE_BUCKETS[h[1] % len(_SIZE_BUCKETS)]
        # Spread employee_count + revenue within the bucket using more bytes.
        employees = bucket[0] + (h[2] % bucket[0])
        revenue = bucket[1] + (int.from_bytes(h[3:6], "big") % bucket[1])

        company = domain_clean.split(".")[0].title()
        return LeadFacts(
            company=company,
            industry=industry,
            employee_count=employees,
            annual_revenue=revenue,
            description=f"{company} is a {industry.lower()} company",
            website=f"https://{domain_clean}",
            linkedin_url=f"https://www.linkedin.com/company/{company.lower()}",
            tags=[industry.lower(), f"size-{bucket[0]}+"],
            provider=self.provider,
            confidence=0.4,  # Fake data, never claim high confidence.
        )

    async def enrich_by_email(self, email: str) -> LeadFacts:
        domain = email.partition("@")[2] if email else ""
        return await self.enrich_by_domain(domain)

    async def close(self) -> None:
        return None


__all__ = ["FakeEnrichmentProvider"]
