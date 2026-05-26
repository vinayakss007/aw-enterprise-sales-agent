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

    # Pipeline ran all four nodes.
    steps = [entry["step"] for entry in result["trajectory"]]
    assert steps == ["research", "enrich", "draft_email", "verify"]
    # Every step recorded as completed.
    assert all(entry["status"] == "completed" for entry in result["trajectory"])
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
    # Execution time is recorded.
    assert result["execution_time_seconds"] >= 0


@pytest.mark.asyncio
async def test_verify_flags_short_body():
    from app.agents.sales_agent.llm import FakeLLM
    from app.agents.sales_agent.nodes import verify_node

    state = {"draft_email": "too short"}
    out = await verify_node(state, FakeLLM())  # type: ignore[arg-type]
    assert "body_too_short" in out["verification_result"]["issues"]
    assert out["verification_result"]["passed"] is False


@pytest.mark.asyncio
async def test_verify_flags_banned_phrase():
    from app.agents.sales_agent.llm import FakeLLM
    from app.agents.sales_agent.nodes import verify_node

    state = {"draft_email": "Hi, please send your password to me right away. " * 3}
    out = await verify_node(state, FakeLLM())  # type: ignore[arg-type]
    assert "body_contains_banned_phrase" in out["verification_result"]["issues"]


def test_openai_pricing_calculation():
    from app.agents.sales_agent.llm import OpenAILLM

    provider = OpenAILLM(api_key="sk-fake", model="gpt-4o-mini")
    # 1M input + 1M output tokens of gpt-4o-mini = 0.15 + 0.60 = $0.75 = 75¢
    assert provider._cost_cents(1_000_000, 1_000_000) == 75
    # Unknown model returns 0 (no surprise charges).
    unknown = OpenAILLM(api_key="sk-fake", model="not-a-real-model")
    assert unknown._cost_cents(1_000_000, 1_000_000) == 0
