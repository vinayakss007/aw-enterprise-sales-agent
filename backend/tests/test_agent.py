"""Tests for the deterministic sales agent."""
import pytest
import pytest_asyncio
from app.agents.sales_agent.agent import SalesAgent
from app.agents.sales_agent.state import AgentState


@pytest.fixture
def basic_state() -> AgentState:
    return AgentState(
        lead_id="test-lead-123",
        lead_email="john@acme.com",
        lead_name="John Smith",
        lead_company="Acme Corp",
        lead_domain="acme.com",
        lead_title="VP of Sales",
        tenant_id="tenant-123",
        user_id="user-123",
        agent_type="research",
        current_step="",
        step_history=[],
        research_results={},
        enriched_data={},
        draft_email="",
        email_subject="",
        score=0,
        success=False,
        error=None,
        execution_time_ms=0,
    )


@pytest.mark.asyncio
class TestSalesAgent:
    async def test_agent_completes_successfully(self, basic_state):
        agent = SalesAgent()
        result = await agent.run(basic_state)

        assert result["success"] is True
        assert result["error"] is None
        assert result["execution_time_ms"] >= 0
        assert len(result["step_history"]) >= 3  # At least research, contact, score

    async def test_agent_researches_company(self, basic_state):
        agent = SalesAgent()
        result = await agent.run(basic_state)

        assert "research_results" in result
        assert result["research_results"].get("domain") == "acme.com"

    async def test_agent_scores_lead(self, basic_state):
        agent = SalesAgent()
        result = await agent.run(basic_state)

        assert "score" in result
        assert 0 <= result["score"] <= 100
        # VP of Sales with business email should score reasonably well
        assert result["score"] >= 30

    async def test_agent_drafts_email_for_research_type(self, basic_state):
        agent = SalesAgent()
        result = await agent.run(basic_state)

        assert result["draft_email"] != ""
        assert result["email_subject"] != ""
        assert "John" in result["draft_email"]

    async def test_agent_no_email_for_follow_up_type(self, basic_state):
        basic_state["agent_type"] = "follow_up"
        agent = SalesAgent()
        result = await agent.run(basic_state)

        # follow_up is in the email template list, so email IS drafted
        assert result["success"] is True

    async def test_agent_handles_minimal_data(self):
        minimal_state = AgentState(
            lead_id="123",
            lead_email="",
            lead_name="",
            lead_company="",
            lead_domain="",
            lead_title="",
            tenant_id="t1",
            user_id="u1",
            agent_type="research",
            current_step="",
            step_history=[],
            research_results={},
            enriched_data={},
            draft_email="",
            email_subject="",
            score=0,
            success=False,
            error=None,
            execution_time_ms=0,
        )
        agent = SalesAgent()
        result = await agent.run(minimal_state)

        assert result["success"] is True
        assert result["score"] == 0  # No data = no score

    async def test_agent_extracts_domain_from_email(self):
        state = AgentState(
            lead_id="123",
            lead_email="contact@newstartup.io",
            lead_name="",
            lead_company="",
            lead_domain="",  # No domain provided
            lead_title="",
            tenant_id="t1",
            user_id="u1",
            agent_type="research",
            current_step="",
            step_history=[],
            research_results={},
            enriched_data={},
            draft_email="",
            email_subject="",
            score=0,
            success=False,
            error=None,
            execution_time_ms=0,
        )
        agent = SalesAgent()
        result = await agent.run(state)

        # Should have researched using domain from email
        assert result["research_results"].get("domain") == "newstartup.io"
