"""Agent execution schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AgentExecutionBase(BaseModel):
    tenant_id: str
    user_id: str
    lead_id: str
    agent_type: str
    # Structured per-step trajectory. Empty list when there is none yet.
    trajectory: list[dict[str, Any]] = []
    success: bool = False
    tokens_input: int = 0
    tokens_output: int = 0
    cost_cents: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None


class AgentExecutionCreate(AgentExecutionBase):
    pass


class AgentExecutionUpdate(BaseModel):
    success: bool | None = None
    cost_cents: int | None = None


class AgentExecutionResponse(AgentExecutionBase):
    id: str
    # Surface the agent's draft outputs so the UI can show them without an
    # extra round-trip.
    draft_subject: str | None = None
    draft_email: str | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
