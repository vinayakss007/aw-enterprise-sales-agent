"""CRM adapter protocol and shared types.

Every CRM integration (HubSpot, Salesforce, Pipedrive, Zoho, Close,
Freshsales, Mock) implements ``CRMAdapter`` so the rest of the application
can be CRM-agnostic. Adapters are picked per tenant by
``app.integrations.crm.factory.get_crm_adapter``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


class CRMError(Exception):
    """Raised by adapters when the upstream CRM is unreachable or rejects a call."""


@dataclass
class CRMContact:
    """Adapter-agnostic contact representation."""

    id: str
    email: str
    name: str | None = None
    company: str | None = None
    properties: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class CRMAdapter(Protocol):
    """Minimal contract every CRM adapter implements."""

    provider: str

    async def upsert_contact(
        self,
        *,
        email: str,
        name: str | None = None,
        company: str | None = None,
        properties: dict[str, Any] | None = None,
    ) -> CRMContact: ...

    async def get_contact(self, contact_id: str) -> CRMContact | None: ...

    async def search_contact_by_email(self, email: str) -> CRMContact | None: ...

    async def create_note(self, contact_id: str, content: str) -> str: ...

    async def close(self) -> None: ...


__all__ = ["CRMAdapter", "CRMContact", "CRMError"]
