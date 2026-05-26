"""In-memory mock CRM adapter.

Used in tests and as the default in dev environments where no real CRM is
configured. Stores contacts and notes in instance dicts so each adapter
instance is isolated.
"""
from __future__ import annotations

import uuid
from typing import Any

from app.integrations.crm.base import CRMAdapter, CRMContact


class MockCRMAdapter(CRMAdapter):
    provider = "mock"

    def __init__(self) -> None:
        self._contacts: dict[str, CRMContact] = {}
        self._email_index: dict[str, str] = {}
        self._notes: dict[str, list[dict[str, Any]]] = {}

    async def upsert_contact(
        self,
        *,
        email: str,
        name: str | None = None,
        company: str | None = None,
        properties: dict[str, Any] | None = None,
    ) -> CRMContact:
        existing_id = self._email_index.get(email.lower())
        if existing_id and existing_id in self._contacts:
            existing = self._contacts[existing_id]
            existing.name = name or existing.name
            existing.company = company or existing.company
            if properties:
                existing.properties.update(properties)
            return existing
        contact = CRMContact(
            id=f"mock_{uuid.uuid4().hex[:12]}",
            email=email,
            name=name,
            company=company,
            properties=dict(properties or {}),
        )
        self._contacts[contact.id] = contact
        self._email_index[email.lower()] = contact.id
        return contact

    async def get_contact(self, contact_id: str) -> CRMContact | None:
        return self._contacts.get(contact_id)

    async def search_contact_by_email(self, email: str) -> CRMContact | None:
        cid = self._email_index.get(email.lower())
        return self._contacts.get(cid) if cid else None

    async def create_note(self, contact_id: str, content: str) -> str:
        if contact_id not in self._contacts:
            from app.integrations.crm.base import CRMError

            raise CRMError(f"contact {contact_id} not found")
        note_id = f"mock_note_{uuid.uuid4().hex[:12]}"
        self._notes.setdefault(contact_id, []).append(
            {"id": note_id, "content": content}
        )
        return note_id

    async def close(self) -> None:
        return None

    # ---- test helpers ----

    def notes_for(self, contact_id: str) -> list[dict[str, Any]]:
        return list(self._notes.get(contact_id, []))


__all__ = ["MockCRMAdapter"]
