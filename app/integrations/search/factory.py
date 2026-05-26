"""Pick a search provider.

Tenant config takes precedence (so a single tenant can use Tavily while
the rest of the platform uses fake), falling back to platform-wide
settings (``SEARCH_PROVIDER``, ``TAVILY_API_KEY``).

Always returns *some* provider — never raises.
"""
from __future__ import annotations

import logging
from typing import Any

from app.core.config import settings
from app.integrations.search.base import SearchProvider
from app.integrations.search.fake import FakeSearchProvider

logger = logging.getLogger(__name__)


def _build(provider: str, credentials: dict[str, Any]) -> SearchProvider | None:
    provider = (provider or "").lower().strip()
    if provider in ("", "fake"):
        return FakeSearchProvider()
    if provider == "tavily":
        from app.integrations.search.tavily import TavilySearchProvider

        api_key = credentials.get("api_key") or getattr(
            settings, "TAVILY_API_KEY", ""
        )
        if not api_key:
            logger.warning("Tavily configured but no api_key provided")
            return None
        return TavilySearchProvider(api_key=api_key)
    logger.warning(
        "Unknown search provider %r — falling back to fake", provider
    )
    return None


def get_search_provider(
    tenant_config: dict[str, Any] | None = None,
) -> SearchProvider:
    section: dict[str, Any] = {}
    if tenant_config:
        section = tenant_config.get("search") or {}

    provider = section.get("provider") or getattr(settings, "SEARCH_PROVIDER", "fake")
    credentials = section.get("credentials") or {}
    return _build(provider, credentials) or FakeSearchProvider()


__all__ = ["get_search_provider"]
