"""Knowledge base CRUD service + tenant-scoped keyword retrieval.

Retrieval is intentionally simple: tokenize the query on whitespace, drop
stopwords, then ``ILIKE`` each token against title + content. Ranking
weights title hits more than content hits and adds a small bonus for
matching tags / category. This is a stand-in until pgvector lands.
"""
from __future__ import annotations

import logging
import re
import uuid
from collections.abc import Iterable
from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.agents.sales_agent.context import KnowledgeLookup, KnowledgeMatch
from app.db.models.knowledge_base import KnowledgeBase
from app.db.models.user import User
from app.schemas.knowledge import (
    KnowledgeCreate,
    KnowledgeResponse,
    KnowledgeUpdate,
)

logger = logging.getLogger(__name__)

_STOPWORDS = frozenset(
    {
        "the", "a", "an", "and", "or", "of", "for", "to", "in", "on", "at",
        "with", "by", "from", "is", "are", "was", "were", "be", "been",
        "this", "that", "these", "those", "it", "its", "we", "you", "they",
    }
)
_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def _tokens(query: str) -> list[str]:
    """Whitespace-tokenize, lowercase, drop stopwords + 1-char tokens."""
    if not query:
        return []
    candidates = (m.group(0).lower() for m in _TOKEN_RE.finditer(query))
    seen: list[str] = []
    seen_set: set[str] = set()
    for token in candidates:
        if len(token) <= 1 or token in _STOPWORDS or token in seen_set:
            continue
        seen.append(token)
        seen_set.add(token)
    return seen


def _score(entry: KnowledgeBase, tokens: Iterable[str]) -> float:
    """Simple weighted score for keyword retrieval.

    * +2 per token found in the title
    * +1 per token found in the content
    * +1 per token matching a tag (case-insensitive)
    * +1 if the category matches any token
    """
    title = (entry.title or "").lower()
    content = (entry.content or "").lower()
    tags = [str(t).lower() for t in (entry.tags or [])]
    category = (entry.category or "").lower()

    score = 0.0
    for token in tokens:
        if token in title:
            score += 2
        if token in content:
            score += 1
        if token in tags:
            score += 1
        if category and token == category:
            score += 1
    return score


class KnowledgeService(KnowledgeLookup):
    """CRUD + retrieval over the ``knowledge_base`` table.

    Implements the ``KnowledgeLookup`` Protocol so it can be plugged
    directly into the agent's ``AgentContext``.
    """

    def __init__(self, db: Session, user: User | None = None):
        self.db = db
        self.user = user
        self.tenant_id = str(user.tenant_id) if user else None

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def list_entries(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
        category: str | None = None,
    ) -> list[KnowledgeResponse]:
        if not self.tenant_id:
            raise ValueError("KnowledgeService.list_entries requires a user")
        query = self.db.query(KnowledgeBase).filter(
            KnowledgeBase.tenant_id == self.tenant_id
        )
        if active_only:
            query = query.filter(KnowledgeBase.active.is_(True))
        if category:
            query = query.filter(KnowledgeBase.category == category)
        rows = (
            query.order_by(KnowledgeBase.updated_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [self._to_response(r) for r in rows]

    async def get_entry(self, entry_id: str) -> KnowledgeResponse | None:
        if not self.tenant_id:
            return None
        row = (
            self.db.query(KnowledgeBase)
            .filter(
                KnowledgeBase.id == entry_id,
                KnowledgeBase.tenant_id == self.tenant_id,
            )
            .first()
        )
        return self._to_response(row) if row else None

    async def create_entry(self, payload: KnowledgeCreate) -> KnowledgeResponse:
        if not self.user:
            raise ValueError("KnowledgeService.create_entry requires a user")
        entry = KnowledgeBase(
            id=uuid.uuid4(),
            tenant_id=self.user.tenant_id,
            created_by=self.user.id,
            title=payload.title,
            content=payload.content,
            category=payload.category,
            tags=payload.tags,
            source=payload.source,
            active=payload.active,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return self._to_response(entry)

    async def update_entry(
        self, entry_id: str, payload: KnowledgeUpdate
    ) -> KnowledgeResponse | None:
        if not self.tenant_id:
            return None
        entry = (
            self.db.query(KnowledgeBase)
            .filter(
                KnowledgeBase.id == entry_id,
                KnowledgeBase.tenant_id == self.tenant_id,
            )
            .first()
        )
        if not entry:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(entry, field, value)
        entry.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(entry)
        return self._to_response(entry)

    async def delete_entry(self, entry_id: str) -> bool:
        if not self.tenant_id:
            return False
        entry = (
            self.db.query(KnowledgeBase)
            .filter(
                KnowledgeBase.id == entry_id,
                KnowledgeBase.tenant_id == self.tenant_id,
            )
            .first()
        )
        if not entry:
            return False
        # Soft delete via the ``active`` flag — keeps history intact and
        # avoids breaking foreign keys from old agent runs that referenced
        # this entry.
        entry.active = False
        entry.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    # ------------------------------------------------------------------
    # KnowledgeLookup Protocol
    # ------------------------------------------------------------------

    async def lookup(
        self, query: str, *, tenant_id: str, limit: int = 3
    ) -> list[KnowledgeMatch]:
        tokens = _tokens(query)
        if not tokens:
            return []
        # Build OR of ILIKE clauses across title + content for each token.
        conditions = []
        for token in tokens:
            like = f"%{token}%"
            conditions.append(KnowledgeBase.title.ilike(like))
            conditions.append(KnowledgeBase.content.ilike(like))

        rows = (
            self.db.query(KnowledgeBase)
            .filter(
                KnowledgeBase.tenant_id == tenant_id,
                KnowledgeBase.active.is_(True),
                or_(*conditions),
            )
            # Pull a generous candidate window; we'll re-rank in-process.
            .limit(50)
            .all()
        )
        if not rows:
            return []

        ranked = sorted(
            ((row, _score(row, tokens)) for row in rows),
            key=lambda pair: pair[1],
            reverse=True,
        )
        out: list[KnowledgeMatch] = []
        for row, score in ranked[:limit]:
            if score <= 0:
                continue
            out.append(
                KnowledgeMatch(
                    id=str(row.id),
                    title=row.title,
                    content=row.content,
                    category=row.category,
                    tags=list(row.tags) if row.tags else None,
                    score=round(score, 3),
                )
            )
        return out

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _to_response(row: KnowledgeBase) -> KnowledgeResponse:
        return KnowledgeResponse(
            id=str(row.id),
            tenant_id=str(row.tenant_id),
            created_by=str(row.created_by) if row.created_by else None,
            title=row.title,
            content=row.content,
            category=row.category,
            tags=list(row.tags) if row.tags else None,
            source=row.source,
            active=row.active,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


__all__ = ["KnowledgeService"]
