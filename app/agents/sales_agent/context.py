"""Per-run context bundle passed to every agent node.

This used to be a bare ``llm`` argument. As the agent grew tools (web
search) and grounding sources (knowledge base), passing each one as a
separate kwarg became noisy. ``AgentContext`` keeps the node signature
small and makes adding the next tool a one-field change.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from app.agents.sales_agent.llm import LLMProvider
from app.integrations.search.base import SearchProvider


@runtime_checkable
class KnowledgeLookup(Protocol):
    """Tenant-scoped retrieval against the knowledge_base table."""

    async def lookup(
        self, query: str, *, tenant_id: str, limit: int = 3
    ) -> list[KnowledgeMatch]: ...


@dataclass
class KnowledgeMatch:
    """A single hit from the knowledge base."""

    id: str
    title: str
    content: str
    category: str | None = None
    tags: list[str] | None = None
    score: float = 0.0


@dataclass
class AgentContext:
    """Everything a node might need to do its job.

    Only ``llm`` is required — ``search`` and ``knowledge`` are optional
    so a minimal test or dev environment can run the pipeline with just
    the LLM.
    """

    llm: LLMProvider
    search: SearchProvider | None = None
    knowledge: KnowledgeLookup | None = None
    # Tenant id is needed by the knowledge lookup; we let the orchestrator
    # set it once rather than re-deriving it inside each node.
    tenant_id: str | None = None


__all__ = ["AgentContext", "KnowledgeLookup", "KnowledgeMatch"]
