"""Pick an enrichment provider.

Tenant config takes precedence (so a single tenant can use Clearbit while
the rest of the platform uses fake), falling back to the platform-wide
``ENRICHMENT_PROVIDER`` setting.

Always returns *some* provider - never raises. Misconfigurations log a
warning and fall back to the fake provider so the rest of the app keeps
working.
"""
from __future__ import annotations

import logging
from typing import Any

from app.core.config import settings
from app.integrations.enrichment.base import EnrichmentProvider
from app.integrations.enrichment.fake import FakeEnrichmentProvider

logger = logging.getLogger(__name__)


def _build(provider: str, credentials: dict[str, Any]) -> EnrichmentProvider | None:
    provider = (provider or "").lower().strip()
    if provider in ("", "fake"):
        return FakeEnrichmentProvider()
    if provider == "clearbit":
        from app.integrations.enrichment.clearbit import ClearbitEnrichmentProvider

        api_key = credentials.get("api_key") or settings.CLEARBIT_API_KEY
        if not api_key:
            logger.warning("Clearbit configured but no api_key provided")
            return None
        return ClearbitEnrichmentProvider(api_key=api_key)
    logger.warning(
        "Unknown enrichment provider %r - falling back to fake", provider
    )
    return None


def get_enrichment_provider(
    tenant_config: dict[str, Any] | None = None,
) -> EnrichmentProvider:
    section: dict[str, Any] = {}
    if tenant_config:
        section = tenant_config.get("enrichment") or {}

    provider = section.get("provider") or getattr(
        settings, "ENRICHMENT_PROVIDER", "fake"
    )
    credentials = section.get("credentials") or {}
    return _build(provider, credentials) or FakeEnrichmentProvider()


__all__ = ["get_enrichment_provider"]
