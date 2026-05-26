"""Knowledge base request / response schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class KnowledgeBase(BaseModel):
    title: str
    content: str
    category: str | None = None
    tags: list[str] | None = None
    source: str | None = None
    active: bool = True


class KnowledgeCreate(KnowledgeBase):
    pass


class KnowledgeUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    source: str | None = None
    active: bool | None = None


class KnowledgeResponse(KnowledgeBase):
    id: str
    tenant_id: str
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeMatchResponse(BaseModel):
    """Returned by the ``/lookup`` debug endpoint."""

    id: str
    title: str
    content: str
    category: str | None = None
    tags: list[str] | None = None
    score: float
