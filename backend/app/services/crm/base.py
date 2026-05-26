"""Abstract CRM adapter interface."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


@dataclass
class CRMContact:
    """Normalized CRM contact representation."""
    id: str
    email: str
    first_name: str = ""
    last_name: str = ""
    company: str = ""
    title: str = ""
    phone: str = ""
    linkedin_url: str = ""
    status: str = "new"
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CRMNote:
    """CRM note/activity representation."""
    id: str
    contact_id: str
    content: str
    note_type: str = "note"  # note, email, call, meeting
    created_at: str = ""


@dataclass
class CRMDeal:
    """CRM deal/opportunity representation."""
    id: str
    contact_id: str
    title: str
    amount_cents: int = 0
    stage: str = "new"
    properties: Dict[str, Any] = field(default_factory=dict)


class CRMAdapter(ABC):
    """
    Abstract base class for CRM integrations.
    Each CRM provider (HubSpot, Salesforce, Pipedrive) implements this interface.
    """

    @abstractmethod
    async def create_contact(self, contact: CRMContact) -> CRMContact:
        """Create a new contact in the CRM."""
        ...

    @abstractmethod
    async def get_contact(self, contact_id: str) -> Optional[CRMContact]:
        """Get a contact by ID."""
        ...

    @abstractmethod
    async def update_contact(self, contact_id: str, updates: Dict[str, Any]) -> CRMContact:
        """Update an existing contact."""
        ...

    @abstractmethod
    async def search_contacts(self, query: str) -> List[CRMContact]:
        """Search contacts by email or name."""
        ...

    @abstractmethod
    async def create_note(self, contact_id: str, content: str, note_type: str = "note") -> CRMNote:
        """Create a note on a contact."""
        ...

    @abstractmethod
    async def get_notes(self, contact_id: str) -> List[CRMNote]:
        """Get all notes for a contact."""
        ...

    @abstractmethod
    async def create_deal(self, deal: CRMDeal) -> CRMDeal:
        """Create a deal/opportunity."""
        ...

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test the CRM connection/credentials."""
        ...
