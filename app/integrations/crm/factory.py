"""Pick a CRM adapter for a given tenant.

Tenant configuration lives in ``Tenant.config['crm']`` and looks like::

    {
        "provider": "hubspot",            # mock | hubspot | ...
        "credentials": {"access_token": "..."}
    }

If no provider is configured (or the configured provider can't be initialised)
we fall back to ``MockCRMAdapter`` so dev/test environments keep working.
"""
from __future__ import annotations

import logging
from typing import Any

from app.core.config import settings
from app.integrations.crm.base import CRMAdapter
from app.integrations.crm.mock import MockCRMAdapter

logger = logging.getLogger(__name__)


def _build_adapter(provider: str, credentials: dict[str, Any]) -> CRMAdapter | None:
    provider = (provider or "").lower().strip()
    if provider in ("", "mock"):
        return MockCRMAdapter()
    if provider == "hubspot":
        from app.integrations.crm.hubspot import HubSpotCRMAdapter

        token = credentials.get("access_token") or credentials.get("token")
        if not token:
            logger.warning("HubSpot CRM configured but no access_token provided")
            return None
        return HubSpotCRMAdapter(access_token=token)
    if provider == "salesforce":
        from app.integrations.crm.salesforce import SalesforceCRMAdapter

        token = credentials.get("access_token") or credentials.get("token")
        instance_url = credentials.get("instance_url")
        if not token or not instance_url:
            logger.warning(
                "Salesforce CRM configured but missing access_token / instance_url"
            )
            return None
        return SalesforceCRMAdapter(
            access_token=token,
            instance_url=instance_url,
            api_version=credentials.get("api_version", "v60.0"),
        )
    logger.warning("Unknown CRM provider %r — falling back to mock", provider)
    return None


def get_crm_adapter(tenant_config: dict[str, Any] | None = None) -> CRMAdapter:
    """Return the CRM adapter selected by the tenant's config.

    Always returns *some* adapter — never raises. Misconfigurations log a
    warning and fall back to the mock so the rest of the request path keeps
    working. Callers that need stricter behaviour can inspect
    ``adapter.provider``.
    """
    crm_section: dict[str, Any] = {}
    if tenant_config:
        crm_section = tenant_config.get("crm") or tenant_config.get("crm_config") or {}

    provider = crm_section.get("provider") or settings.DEFAULT_CRM_PROVIDER
    credentials = crm_section.get("credentials") or {}
    adapter = _build_adapter(provider, credentials)
    return adapter or MockCRMAdapter()


__all__ = ["get_crm_adapter"]
