"""Enrichment Protocol + shared types."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


class EnrichmentError(Exception):
    """Raised when an enrichment provider fails (transport, auth, rate limit)."""


@dataclass
class LeadFacts:
    """Provider-agnostic enrichment payload merged into ``Lead.enriched_data``.

    All fields are optional — providers fill in what they can. The
    ``provider`` and ``confidence`` fields are bookkeeping that the service
    layer uses to decide whether to overwrite a previous enrichment.
    """

    company: str | None = None
    industry: str | None = None
    employee_count: int | None = None
    annual_revenue: int | None = None
    description: str | None = None
    headquarters: str | None = None
    website: str | None = None
    linkedin_url: str | None = None
    twitter_handle: str | None = None
    technologies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    provider: str = ""
    confidence: float = 0.0  # 0.0 (no info) -> 1.0 (authoritative)

    def to_dict(self) -> dict[str, Any]:
        """JSON-safe dict for persistence in ``Lead.enriched_data``."""
        return {
            "company": self.company,
            "industry": self.industry,
            "employee_count": self.employee_count,
            "annual_revenue": self.annual_revenue,
            "description": self.description,
            "headquarters": self.headquarters,
            "website": self.website,
            "linkedin_url": self.linkedin_url,
            "twitter_handle": self.twitter_handle,
            "technologies": list(self.technologies),
            "tags": list(self.tags),
            "extra": dict(self.extra),
            "provider": self.provider,
            "confidence": self.confidence,
        }


@runtime_checkable
class EnrichmentProvider(Protocol):
    provider: str

    async def enrich_by_domain(self, domain: str) -> LeadFacts: ...

    async def enrich_by_email(self, email: str) -> LeadFacts: ...

    async def close(self) -> None: ...


__all__ = ["EnrichmentError", "EnrichmentProvider", "LeadFacts"]
