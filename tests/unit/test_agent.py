"""Sales agent — pipeline behaviour with FakeLLM."""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_fake_llm_returns_deterministic_output():
    from app.agents.sales_agent.llm import FakeLLM

    llm = FakeLLM()
    a = await llm.complete([{"role": "user", "content": "hello there"}])
    b = await llm.complete([{"role": "user", "content": "hello there"}])
    assert a.content == b.content
    assert a.tokens_input >= 1
    assert a.tokens_output >= 1
    assert a.cost_cents == 0


@pytest.mark.asyncio
async def test_get_llm_falls_back_to_fake_without_key(monkeypatch):
    from app.agents.sales_agent import llm as llm_mod

    monkeypatch.setattr(llm_mod.settings, "OPENAI_API_KEY", "")
    monkeypatch.setattr(llm_mod.settings, "LLM_PROVIDER", "openai")
    provider = llm_mod.get_llm()
    assert isinstance(provider, llm_mod.FakeLLM)


@pytest.mark.asyncio
async def test_sales_agent_full_pipeline_with_fake_llm():
    """Default pipeline with no search / knowledge: knowledge node skips."""
    from app.agents.sales_agent.graph import SalesAgent
    from app.agents.sales_agent.llm import FakeLLM

    agent = SalesAgent(llm=FakeLLM())
    initial = {
        "lead": {
            "id": "lead-1",
            "email": "ceo@target.test",
            "name": "Pat Patterson",
            "company": "Target Inc",
            "domain": "target.test",
            "title": "CEO",
        },
        "user_id": "u1",
        "tenant_id": "t1",
        "agent_type": "research",
    }
    result = await agent.run(initial)

    # Pipeline now has five nodes; knowledge skips because no provider.
    steps = [entry["step"] for entry in result["trajectory"]]
    assert steps == ["research", "enrich", "knowledge", "draft_email", "verify"]
    statuses = {entry["step"]: entry["status"] for entry in result["trajectory"]}
    assert statuses["research"] == "completed"
    assert statuses["enrich"] == "completed"
    assert statuses["knowledge"] == "skipped"  # no provider
    assert statuses["draft_email"] == "completed"
    assert statuses["verify"] == "completed"

    # Draft outputs populated.
    assert result["draft_subject"]
    assert len(result["draft_email"]) >= 30
    # Aggregate accounting is non-zero and matches sum-of-entries.
    assert result["tokens_input"] >= 1
    assert result["tokens_output"] >= 1
    summed_in = sum(e.get("tokens_input", 0) for e in result["trajectory"])
    summed_out = sum(e.get("tokens_output", 0) for e in result["trajectory"])
    assert result["tokens_input"] == summed_in
    assert result["tokens_output"] == summed_out
    # Verification passed → success is True.
    assert result["verification_result"]["passed"] is True
    assert result["success"] is True
    assert result["error"] is None


@pytest.mark.asyncio
async def test_research_node_uses_search_provider_when_supplied():
    """Search hits should land in research_results.search and the trajectory."""
    from app.agents.sales_agent.context import AgentContext
    from app.agents.sales_agent.llm import FakeLLM
    from app.agents.sales_agent.nodes import research_node
    from app.integrations.search.fake import FakeSearchProvider

    state = {
        "lead": {"company": "Target Inc", "domain": "target.test", "title": "CEO"},
        "trajectory": [],
        "tokens_input": 0,
        "tokens_output": 0,
        "cost_cents": 0,
    }
    ctx = AgentContext(llm=FakeLLM(), search=FakeSearchProvider())
    out = await research_node(state, ctx)

    assert out["research_results"]["search"]
    assert len(out["research_results"]["search"]) >= 1
    research_entry = next(e for e in out["trajectory"] if e["step"] == "research")
    assert research_entry["details"]["search_provider"] == "fake"
    assert research_entry["details"]["search_results"] >= 1


@pytest.mark.asyncio
async def test_knowledge_node_runs_when_provider_supplied():
    """A KnowledgeLookup with hits puts results into knowledge_results."""
    from app.agents.sales_agent.context import AgentContext, KnowledgeMatch
    from app.agents.sales_agent.llm import FakeLLM
    from app.agents.sales_agent.nodes import knowledge_node

    class StubKnowledge:
        async def lookup(self, query, *, tenant_id, limit=3):
            assert tenant_id == "t1"
            return [
                KnowledgeMatch(
                    id="k1", title="Pricing", content="Our plans start at $99",
                    category="pricing", tags=["pricing"], score=3.0,
                )
            ]

    state = {
        "lead": {"company": "Target Inc", "title": "CEO"},
        "trajectory": [],
        "tokens_input": 0,
        "tokens_output": 0,
        "cost_cents": 0,
    }
    ctx = AgentContext(llm=FakeLLM(), knowledge=StubKnowledge(), tenant_id="t1")
    out = await knowledge_node(state, ctx)

    assert len(out["knowledge_results"]) == 1
    assert out["knowledge_results"][0]["title"] == "Pricing"
    knowledge_entry = next(e for e in out["trajectory"] if e["step"] == "knowledge")
    assert knowledge_entry["status"] == "completed"
    assert knowledge_entry["details"]["matches"] == 1


@pytest.mark.asyncio
async def test_knowledge_node_skips_when_no_provider():
    from app.agents.sales_agent.context import AgentContext
    from app.agents.sales_agent.llm import FakeLLM
    from app.agents.sales_agent.nodes import knowledge_node

    state = {
        "lead": {"company": "Target Inc"},
        "trajectory": [],
        "tokens_input": 0,
        "tokens_output": 0,
        "cost_cents": 0,
    }
    out = await knowledge_node(state, AgentContext(llm=FakeLLM()))
    entry = next(e for e in out["trajectory"] if e["step"] == "knowledge")
    assert entry["status"] == "skipped"
    assert "knowledge_results" not in out


@pytest.mark.asyncio
async def test_draft_email_includes_knowledge_results_in_prompt():
    """When knowledge_results is populated, draft_email should reference them."""
    from app.agents.sales_agent.context import AgentContext
    from app.agents.sales_agent.llm import FakeLLM
    from app.agents.sales_agent.nodes import draft_email_node

    captured_messages: list[list[dict]] = []

    class CaptureLLM(FakeLLM):
        async def complete(self, messages, *, max_tokens=512, temperature=0.4):
            captured_messages.append(messages)
            return await super().complete(
                messages, max_tokens=max_tokens, temperature=temperature
            )

    state = {
        "lead": {"name": "Pat", "company": "Target"},
        "research_results": {"summary": "tech company"},
        "knowledge_results": [
            {"title": "Pricing", "content": "Plans from $99/mo"},
            {"title": "Onboarding", "content": "Activation in 24h"},
        ],
        "trajectory": [],
        "tokens_input": 0,
        "tokens_output": 0,
        "cost_cents": 0,
    }
    out = await draft_email_node(state, AgentContext(llm=CaptureLLM()))

    assert captured_messages, "expected the LLM to be called"
    user_prompt = captured_messages[0][-1]["content"]
    assert "Pricing" in user_prompt
    assert "Onboarding" in user_prompt
    draft_entry = next(e for e in out["trajectory"] if e["step"] == "draft_email")
    assert draft_entry["details"]["knowledge_used"] == 2


@pytest.mark.asyncio
async def test_verify_flags_short_body():
    from app.agents.sales_agent.context import AgentContext
    from app.agents.sales_agent.llm import FakeLLM
    from app.agents.sales_agent.nodes import verify_node

    state = {"draft_email": "too short"}
    out = await verify_node(state, AgentContext(llm=FakeLLM()))  # type: ignore[arg-type]
    assert "body_too_short" in out["verification_result"]["issues"]
    assert out["verification_result"]["passed"] is False


@pytest.mark.asyncio
async def test_verify_flags_banned_phrase():
    from app.agents.sales_agent.context import AgentContext
    from app.agents.sales_agent.llm import FakeLLM
    from app.agents.sales_agent.nodes import verify_node

    state = {"draft_email": "Hi, please send your password to me right away. " * 3}
    out = await verify_node(state, AgentContext(llm=FakeLLM()))  # type: ignore[arg-type]
    assert "body_contains_banned_phrase" in out["verification_result"]["issues"]


def test_openai_pricing_calculation():
    from app.agents.sales_agent.llm import OpenAILLM

    provider = OpenAILLM(api_key="sk-fake", model="gpt-4o-mini")
    # 1M input + 1M output tokens of gpt-4o-mini = 0.15 + 0.60 = $0.75 = 75¢
    assert provider._cost_cents(1_000_000, 1_000_000) == 75
    # Unknown model returns 0 (no surprise charges).
    unknown = OpenAILLM(api_key="sk-fake", model="not-a-real-model")
    assert unknown._cost_cents(1_000_000, 1_000_000) == 0
