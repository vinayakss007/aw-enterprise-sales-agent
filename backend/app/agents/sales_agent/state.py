"""Agent execution state definition."""
from typing import TypedDict, Optional, Dict, Any, List
from datetime import datetime


class StepResult(TypedDict, total=False):
    step: str
    status: str  # completed, failed, skipped
    timestamp: str
    details: str
    data: Dict[str, Any]


class AgentState(TypedDict, total=False):
    # Input
    lead_id: str
    lead_email: str
    lead_name: str
    lead_company: str
    lead_domain: str
    lead_title: str
    tenant_id: str
    user_id: str
    agent_type: str  # research, outreach, follow_up

    # Workflow state
    current_step: str
    step_history: List[StepResult]

    # Results
    research_results: Dict[str, Any]
    enriched_data: Dict[str, Any]
    draft_email: str
    email_subject: str
    score: int  # lead score 0-100

    # Execution metadata
    started_at: str
    completed_at: str
    success: bool
    error: Optional[str]
    execution_time_ms: int
