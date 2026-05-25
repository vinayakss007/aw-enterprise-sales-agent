"""Customer-side agent service: kicks off agent runs, persists results."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.agents.sales_agent.graph import SalesAgent
from app.agents.sales_agent.state import AgentState
from app.db.models.agent_execution import AgentExecution
from app.db.models.lead import Lead
from app.db.models.user import User
from app.schemas.agent import AgentExecutionResponse


def _lead_to_dict(lead: Lead) -> dict[str, Any]:
    """Plain-dict snapshot of a lead — agent state is JSON-serialised."""
    return {
        "id": str(lead.id),
        "email": lead.email,
        "name": lead.name,
        "company": lead.company,
        "domain": lead.domain,
        "title": lead.title,
        "linkedin_url": lead.linkedin_url,
        "phone": lead.phone,
    }


class AgentService:
    """Thin façade around ``SalesAgent`` that owns DB persistence."""

    def __init__(
        self,
        db: Session,
        user: User,
        agent: SalesAgent | None = None,
    ) -> None:
        self.db = db
        self.user = user
        self.tenant_id = user.tenant_id
        # Allow tests / callers to inject a custom agent (e.g. with a stubbed
        # LLM provider). The default uses ``get_llm()``.
        self.agent = agent or SalesAgent()

    async def execute_agent(
        self, lead_id: str, agent_type: str = "research"
    ) -> AgentExecutionResponse | None:
        lead = (
            self.db.query(Lead)
            .filter(Lead.id == lead_id, Lead.tenant_id == self.tenant_id)
            .first()
        )
        if not lead:
            return None

        initial_state: AgentState = {
            "lead": _lead_to_dict(lead),
            "user_id": str(self.user.id),
            "tenant_id": str(self.tenant_id),
            "agent_type": agent_type,
            "current_step": "initialized",
            "trajectory": [],
            "research_results": {},
            "enriched_data": {},
            "draft_email": "",
            "draft_subject": "",
            "verification_result": {},
            "tokens_input": 0,
            "tokens_output": 0,
            "cost_cents": 0,
            "execution_time_seconds": 0.0,
            "success": False,
            "error": None,
        }

        started_at = datetime.utcnow()
        result = await self.agent.run(initial_state)
        completed_at = datetime.utcnow()

        execution = AgentExecution(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            user_id=self.user.id,
            lead_id=lead.id,
            agent_type=agent_type,
            trajectory=result.get("trajectory", []),
            success=bool(result.get("success", False)),
            tokens_input=int(result.get("tokens_input", 0)),
            tokens_output=int(result.get("tokens_output", 0)),
            cost_cents=int(result.get("cost_cents", 0)),
            started_at=started_at,
            completed_at=completed_at,
        )
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)

        return self._to_response(
            execution,
            draft_subject=result.get("draft_subject", ""),
            draft_email=result.get("draft_email", ""),
            error=result.get("error"),
        )

    async def get_executions(
        self, skip: int = 0, limit: int = 50
    ) -> list[AgentExecutionResponse]:
        executions = (
            self.db.query(AgentExecution)
            .filter(
                AgentExecution.tenant_id == self.tenant_id,
                AgentExecution.user_id == self.user.id,
            )
            .order_by(AgentExecution.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [self._to_response(execution) for execution in executions]

    async def get_execution(
        self, execution_id: str
    ) -> AgentExecutionResponse | None:
        execution = (
            self.db.query(AgentExecution)
            .filter(
                AgentExecution.id == execution_id,
                AgentExecution.tenant_id == self.tenant_id,
            )
            .first()
        )
        if not execution:
            return None
        return self._to_response(execution)

    @staticmethod
    def _to_response(
        execution: AgentExecution,
        *,
        draft_subject: str = "",
        draft_email: str = "",
        error: str | None = None,
    ) -> AgentExecutionResponse:
        trajectory = execution.trajectory or []
        # Pull the draft fields from the trajectory if not passed in.
        if not draft_subject or not draft_email:
            for entry in trajectory:
                if entry.get("step") == "draft_email" and isinstance(
                    entry.get("details"), dict
                ):
                    draft_subject = draft_subject or entry["details"].get(
                        "subject", ""
                    )
                    break
        return AgentExecutionResponse(
            id=str(execution.id),
            tenant_id=str(execution.tenant_id),
            user_id=str(execution.user_id),
            lead_id=str(execution.lead_id),
            agent_type=execution.agent_type,
            trajectory=trajectory,
            success=execution.success,
            tokens_input=execution.tokens_input,
            tokens_output=execution.tokens_output,
            cost_cents=execution.cost_cents,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            draft_subject=draft_subject or None,
            draft_email=draft_email or None,
            error=error,
            created_at=execution.created_at,
            updated_at=execution.updated_at,
        )
