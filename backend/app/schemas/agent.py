"""Agent execution schemas."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AgentExecutionResponse(BaseModel):
    id: str
    tenant_id: str
    user_id: str
    lead_id: str
    agent_type: str
    trajectory: Optional[str] = None
    success: bool
    tokens_input: int = 0
    tokens_output: int = 0
    cost_cents: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
