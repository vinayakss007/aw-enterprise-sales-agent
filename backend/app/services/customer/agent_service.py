"""Agent execution service - orchestrates the deterministic sales agent."""
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.db.models.lead import Lead
from app.db.models.agent_execution import AgentExecution
from app.schemas.agent import AgentExecutionResponse
from app.agents.sales_agent import SalesAgent
from app.agents.sales_agent.state import AgentState


class AgentService:
    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.tenant_id = user.tenant_id

    async def execute_agent(self, lead_id: str, agent_type: str = "research") -> Optional[AgentExecutionResponse]:
        """Execute the sales agent for a specific lead."""
        # Fetch the lead
        lead = self.db.query(Lead).filter(
            Lead.id == lead_id,
            Lead.tenant_id == self.tenant_id,
        ).first()

        if not lead:
            return None

        # Build initial state from lead data
        initial_state: AgentState = {
            "lead_id": str(lead.id),
            "lead_email": lead.email or "",
            "lead_name": lead.name or "",
            "lead_company": lead.company or "",
            "lead_domain": lead.domain or "",
            "lead_title": lead.title or "",
            "tenant_id": str(self.tenant_id),
            "user_id": str(self.user.id),
            "agent_type": agent_type,
            "current_step": "initialized",
            "step_history": [],
            "research_results": {},
            "enriched_data": {},
            "draft_email": "",
            "email_subject": "",
            "score": 0,
            "success": False,
            "error": None,
            "execution_time_ms": 0,
        }

        # Execute the agent
        agent = SalesAgent()
        start_time = datetime.utcnow()
        result = await agent.run(initial_state)

        # Update lead with enriched data if successful
        if result.get("success"):
            if result.get("enriched_data"):
                lead.enriched_data = {**(lead.enriched_data or {}), **result["enriched_data"]}
            lead.updated_at = datetime.utcnow()

        # Persist execution record
        execution = AgentExecution(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            user_id=self.user.id,
            lead_id=lead.id,
            agent_type=agent_type,
            trajectory=result.get("step_history", []),
            success=result.get("success", False),
            tokens_input=0,  # Deterministic agent uses no tokens
            tokens_output=0,
            cost_cents=0,
            started_at=start_time,
            completed_at=datetime.utcnow(),
            error_message=result.get("error"),
        )

        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)

        return self._to_response(execution)

    async def get_executions(self, skip: int = 0, limit: int = 50) -> List[AgentExecutionResponse]:
        """Get agent execution history."""
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
        return [self._to_response(ex) for ex in executions]

    async def get_execution(self, execution_id: str) -> Optional[AgentExecutionResponse]:
        """Get specific execution."""
        execution = self.db.query(AgentExecution).filter(
            AgentExecution.id == execution_id,
            AgentExecution.tenant_id == self.tenant_id,
        ).first()
        return self._to_response(execution) if execution else None

    def _to_response(self, ex: AgentExecution) -> AgentExecutionResponse:
        return AgentExecutionResponse(
            id=str(ex.id),
            tenant_id=str(ex.tenant_id),
            user_id=str(ex.user_id),
            lead_id=str(ex.lead_id),
            agent_type=ex.agent_type,
            trajectory=str(ex.trajectory) if ex.trajectory else "",
            success=ex.success,
            tokens_input=ex.tokens_input,
            tokens_output=ex.tokens_output,
            cost_cents=ex.cost_cents,
            started_at=ex.started_at,
            completed_at=ex.completed_at,
            created_at=ex.created_at,
            updated_at=ex.updated_at,
        )
