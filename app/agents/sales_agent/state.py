"""Agent state types.

The state is a plain ``TypedDict`` so it round-trips cleanly through JSON
serialization (we persist parts of it to a JSONB column).
"""
from __future__ import annotations

from typing import Any, TypedDict


class TrajectoryEntry(TypedDict, total=False):
    step: str
    status: str  # "started" | "completed" | "failed" | "skipped"
    started_at: float
    completed_at: float
    duration_ms: int
    details: dict[str, Any]
    tokens_input: int
    tokens_output: int
    cost_cents: int
    model: str
    error: str


class AgentState(TypedDict, total=False):
    # ---- Inputs ----
    lead: dict[str, Any]  # serialized lead, not the ORM object
    user_id: str
    tenant_id: str
    agent_type: str  # research | outreach | follow-up

    # ---- Working memory ----
    research_results: dict[str, Any]
    enriched_data: dict[str, Any]
    draft_email: str
    draft_subject: str
    verification_result: dict[str, Any]

    # ---- Execution context ----
    current_step: str
    trajectory: list[TrajectoryEntry]

    # ---- Aggregates filled in by the orchestrator ----
    tokens_input: int
    tokens_output: int
    cost_cents: int
    execution_time_seconds: float
    success: bool
    error: str | None
