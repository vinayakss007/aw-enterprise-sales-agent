"""CRM integration service with adapter pattern."""
from app.services.crm.base import CRMAdapter, CRMContact, CRMNote
from app.services.crm.factory import get_crm_adapter

__all__ = ["CRMAdapter", "CRMContact", "CRMNote", "get_crm_adapter"]
