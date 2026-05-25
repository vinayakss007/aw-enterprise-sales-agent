"""Sales agent orchestrator.

Runs nodes in sequence on a shared ``AgentState`` and computes top-level
aggregates (success/error, totals, execution time).

The default pipeline is ``research → enrich → knowledge → draft → verify``.
The ``knowledge`` node skips when no ``KnowledgeLookup`` is wired into the
context, so callers without a DB still get a working pipeline.

Every node has the ``(state, ctx) -> state`` signature, so swapping in a
real LangGraph ``StateGraph`` later does not require changing the nodes.
"""
from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable

from app.agents.sales_agent.context import AgentContext, KnowledgeLookup
from app.agents.sales_agent.llm import LLMProvider, get_llm
from app.agents.sales_agent.nodes import (
    draft_email_node,
    enrich_node,
    knowledge_node,
    research_node,
    verify_node,
)
from app.agents.sales_agent.state import AgentState
from app.integrations.search.base import SearchProvider

logger = logging.getLogger(__name__)

NodeFn = Callable[[AgentState, AgentContext], Awaitable[AgentState]]

DEFAULT_PIPELINE: list[NodeFn] = [
    research_node,
    enrich_node,
    knowledge_node,
    draft_email_node,
    verify_node,
]


class SalesAgent:
    """Sequential async orchestrator for the agent pipeline."""

    def __init__(
        self,
        llm: LLMProvider | None = None,
        *,
        search: SearchProvider | None = None,
        knowledge: KnowledgeLookup | None = None,
        pipeline: list[NodeFn] | None = None,
    ) -> None:
        self.llm: LLMProvider = llm or get_llm()
        self.search = search
        self.knowledge = knowledge
        self.pipeline: list[NodeFn] = pipeline or DEFAULT_PIPELINE

    async def run(self, state: AgentState) -> AgentState:
        # Defaults so caller doesn't have to seed every key.
        state.setdefault("trajectory", [])
        state.setdefault("tokens_input", 0)
        state.setdefault("tokens_output", 0)
        state.setdefault("cost_cents", 0)
        state.setdefault("error", None)

        ctx = AgentContext(
            llm=self.llm,
            search=self.search,
            knowledge=self.knowledge,
            tenant_id=str(state.get("tenant_id") or "") or None,
        )

        start = time.perf_counter()
        try:
            for node in self.pipeline:
                state = await node(state, ctx)
                if state.get("error"):
                    # Stop on first error but keep the trajectory entries we have.
                    break
        except Exception as exc:  # pragma: no cover — defensive
            logger.exception("SalesAgent.run crashed")
            state["error"] = f"unhandled: {exc}"
        elapsed = time.perf_counter() - start

        verification = state.get("verification_result") or {}
        state["execution_time_seconds"] = round(elapsed, 3)
        state["success"] = state.get("error") is None and verification.get(
            "passed", True
        )
        return state


__all__ = ["SalesAgent", "DEFAULT_PIPELINE"]
