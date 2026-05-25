"""CRM integrations package."""
from app.integrations.crm.base import CRMAdapter, CRMContact, CRMError
from app.integrations.crm.factory import get_crm_adapter

__all__ = ["CRMAdapter", "CRMContact", "CRMError", "get_crm_adapter"]
