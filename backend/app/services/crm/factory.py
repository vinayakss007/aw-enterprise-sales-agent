"""CRM adapter factory - returns the appropriate adapter based on config."""
import logging
from app.services.crm.base import CRMAdapter
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_crm_adapter(provider: str = None, api_key: str = None) -> CRMAdapter:
    """
    Factory function to get the appropriate CRM adapter.

    Args:
        provider: CRM provider name (hubspot, salesforce, pipedrive). Defaults to settings.
        api_key: API key override. Defaults to settings.
    """
    provider = provider or settings.DEFAULT_CRM_PROVIDER

    if provider == "hubspot":
        from app.services.crm.hubspot import HubSpotAdapter
        key = api_key or settings.HUBSPOT_API_KEY
        if not key:
            raise ValueError("HUBSPOT_API_KEY not configured")
        return HubSpotAdapter(api_key=key)
    elif provider == "salesforce":
        # Salesforce adapter would go here
        raise NotImplementedError(f"Salesforce adapter not yet implemented")
    elif provider == "pipedrive":
        # Pipedrive adapter would go here
        raise NotImplementedError(f"Pipedrive adapter not yet implemented")
    else:
        raise ValueError(f"Unknown CRM provider: {provider}")
