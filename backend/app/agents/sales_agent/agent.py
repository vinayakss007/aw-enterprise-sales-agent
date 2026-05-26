"""
Deterministic Sales Agent — real implementation.
Executes a multi-step workflow: research -> enrich -> score -> draft email.
No AI on the critical path. All steps are deterministic with rule-based logic.
"""
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any

from app.agents.sales_agent.state import AgentState, StepResult
from app.agents.sales_agent.research import research_company, research_contact
from app.agents.sales_agent.scoring import score_lead, get_score_label
from app.agents.sales_agent.email_drafter import draft_email

logger = logging.getLogger(__name__)


class SalesAgent:
    """
    Deterministic sales agent that executes a multi-step workflow:
    1. Research the lead's company (domain lookup, Clearbit enrichment)
    2. Research the contact (email validation, classification)
    3. Score the lead (rule-based scoring engine)
    4. Draft outreach email (template-based with personalization)
    """

    async def run(self, state: AgentState) -> AgentState:
        """
        Execute the full agent workflow.
        Returns the updated state with results from each step.
        """
        start_time = time.time()
        state["started_at"] = datetime.now(timezone.utc).isoformat()
        state["step_history"] = []
        state["success"] = False
        state["error"] = None

        try:
            # Step 1: Research company
            state = await self._step_research_company(state)

            # Step 2: Research contact
            state = await self._step_research_contact(state)

            # Step 3: Score lead
            state = await self._step_score_lead(state)

            # Step 4: Draft email (only for outreach/research agent types)
            if state.get("agent_type") in ("research", "outreach", "cold_outreach"):
                state = await self._step_draft_email(state)

            state["success"] = True

        except Exception as e:
            logger.error(f"Agent execution failed: {e}", exc_info=True)
            state["error"] = str(e)
            state["step_history"].append(StepResult(
                step="error",
                status="failed",
                timestamp=datetime.now(timezone.utc).isoformat(),
                details=str(e),
                data={},
            ))

        elapsed_ms = int((time.time() - start_time) * 1000)
        state["execution_time_ms"] = elapsed_ms
        state["completed_at"] = datetime.now(timezone.utc).isoformat()

        return state

    async def _step_research_company(self, state: AgentState) -> AgentState:
        """Step 1: Research the lead's company by domain."""
        state["current_step"] = "research_company"
        domain = state.get("lead_domain", "")

        # If no domain, try to extract from email
        if not domain and state.get("lead_email"):
            email = state["lead_email"]
            if "@" in email:
                domain = email.split("@")[-1]

        research_results = {}
        if domain:
            research_results = await research_company(domain)

        state["research_results"] = research_results
        state["step_history"].append(StepResult(
            step="research_company",
            status="completed",
            timestamp=datetime.now(timezone.utc).isoformat(),
            details=f"Researched domain: {domain}",
            data=research_results,
        ))

        return state

    async def _step_research_contact(self, state: AgentState) -> AgentState:
        """Step 2: Research/validate the contact."""
        state["current_step"] = "research_contact"

        contact_data = await research_contact(
            email=state.get("lead_email", ""),
            name=state.get("lead_name", ""),
        )

        # Merge into enriched data
        enriched = state.get("enriched_data", {})
        enriched.update(contact_data)
        state["enriched_data"] = enriched

        state["step_history"].append(StepResult(
            step="research_contact",
            status="completed",
            timestamp=datetime.now(timezone.utc).isoformat(),
            details=f"Researched contact: {state.get('lead_email', '')}",
            data=contact_data,
        ))

        return state

    async def _step_score_lead(self, state: AgentState) -> AgentState:
        """Step 3: Score the lead using rule-based engine."""
        state["current_step"] = "score_lead"

        score = score_lead(
            email=state.get("lead_email", ""),
            company=state.get("lead_company", ""),
            title=state.get("lead_title", ""),
            linkedin_url="",  # Would come from lead data
            phone="",
            research_data=state.get("research_results", {}),
        )

        state["score"] = score
        label = get_score_label(score)

        state["step_history"].append(StepResult(
            step="score_lead",
            status="completed",
            timestamp=datetime.now(timezone.utc).isoformat(),
            details=f"Lead scored: {score}/100 ({label})",
            data={"score": score, "label": label},
        ))

        return state

    async def _step_draft_email(self, state: AgentState) -> AgentState:
        """Step 4: Draft outreach email using templates."""
        state["current_step"] = "draft_email"

        agent_type = state.get("agent_type", "research")
        template_map = {
            "research": "research_intro",
            "outreach": "cold_outreach",
            "cold_outreach": "cold_outreach",
            "follow_up": "follow_up",
        }
        template_type = template_map.get(agent_type, "research_intro")

        email_result = draft_email(
            template_type=template_type,
            lead_name=state.get("lead_name", ""),
            lead_company=state.get("lead_company", ""),
            lead_title=state.get("lead_title", ""),
            research_data=state.get("research_results", {}),
        )

        state["draft_email"] = email_result["body"]
        state["email_subject"] = email_result["subject"]

        state["step_history"].append(StepResult(
            step="draft_email",
            status="completed",
            timestamp=datetime.now(timezone.utc).isoformat(),
            details=f"Drafted {template_type} email",
            data={"subject": email_result["subject"]},
        ))

        return state
