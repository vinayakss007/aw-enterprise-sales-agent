"""Sales agent orchestrator.

Runs the four nodes (``research → enrich → draft_email → verify``) in
sequence on a shared ``AgentState`` and computes top-level aggregates
(success/error, totals, execution time).

The shape is deliberately compatible with LangGraph: every node has the same
``(state, llm) -> state`` signature, so swapping in a real
``StateGraph`` later does not require changing the nodes.
"""
from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable

from app.agents.sales_agent.llm import LLMProvider, get_llm
from app.agents.sales_agent.nodes import (
    draft_email_node,
    enrich_node,
    research_node,
    verify_node,
)
from app.agents.sales_agent.state import AgentState

logger = logging.getLogger(__name__)

NodeFn = Callable[[AgentState, LLMProvider], Awaitable[AgentState]]

DEFAULT_PIPELINE: list[NodeFn] = [
    research_node,
    enrich_node,
    draft_email_node,
    verify_node,
]


class SalesAgent:
    """Sequential async orchestrator for the four sales-agent nodes."""

    def __init__(
        self,
        llm: LLMProvider | None = None,
        pipeline: list[NodeFn] | None = None,
    ) -> None:
        self.llm: LLMProvider = llm or get_llm()
        self.pipeline: list[NodeFn] = pipeline or DEFAULT_PIPELINE

    async def run(self, state: AgentState) -> AgentState:
        # Defaults so caller doesn't have to seed every key.
        state.setdefault("trajectory", [])
        state.setdefault("tokens_input", 0)
        state.setdefault("tokens_output", 0)
        state.setdefault("cost_cents", 0)
        state.setdefault("error", None)

        start = time.perf_counter()
        try:
            for node in self.pipeline:
                state = await node(state, self.llm)
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
