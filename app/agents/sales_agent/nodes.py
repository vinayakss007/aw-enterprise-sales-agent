"""Agent nodes.

Each node:
  * is an ``async`` function ``(state, llm) -> state``
  * mutates the supplied state in-place (and returns it for chaining)
  * appends a structured ``TrajectoryEntry`` describing what happened
  * never raises through to the caller — it sets ``state['error']`` instead so
    the orchestrator can decide how to handle it.

This shape is compatible with LangGraph nodes and can be dropped into a
LangGraph ``StateGraph`` later without changing the function signatures.
"""
from __future__ import annotations

import logging
import time
from typing import Any

from app.agents.sales_agent.llm import LLMProvider, LLMResult
from app.agents.sales_agent.state import AgentState, TrajectoryEntry

logger = logging.getLogger(__name__)


def _record(state: AgentState, entry: TrajectoryEntry) -> None:
    state.setdefault("trajectory", []).append(entry)
    state["tokens_input"] = state.get("tokens_input", 0) + entry.get("tokens_input", 0)
    state["tokens_output"] = state.get("tokens_output", 0) + entry.get("tokens_output", 0)
    state["cost_cents"] = state.get("cost_cents", 0) + entry.get("cost_cents", 0)


def _start_entry(step: str) -> TrajectoryEntry:
    return TrajectoryEntry(step=step, status="started", started_at=time.time())


def _complete_entry(
    entry: TrajectoryEntry,
    *,
    details: dict[str, Any] | None = None,
    llm: LLMResult | None = None,
) -> TrajectoryEntry:
    entry["status"] = "completed"
    entry["completed_at"] = time.time()
    entry["duration_ms"] = int((entry["completed_at"] - entry["started_at"]) * 1000)
    if details is not None:
        entry["details"] = details
    if llm is not None:
        entry["tokens_input"] = llm.tokens_input
        entry["tokens_output"] = llm.tokens_output
        entry["cost_cents"] = llm.cost_cents
        entry["model"] = llm.model
    return entry


def _fail_entry(entry: TrajectoryEntry, exc: BaseException) -> TrajectoryEntry:
    entry["status"] = "failed"
    entry["completed_at"] = time.time()
    entry["duration_ms"] = int((entry["completed_at"] - entry["started_at"]) * 1000)
    entry["error"] = f"{type(exc).__name__}: {exc}"
    return entry


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


async def research_node(state: AgentState, llm: LLMProvider) -> AgentState:
    """Gather a brief profile of the target company.

    Today this is purely a one-shot LLM call. Later this is the natural place
    to wire in a search tool (SerpAPI, Tavily, Bing) so the model has fresh
    facts to ground its summary.
    """
    state["current_step"] = "research"
    entry = _start_entry("research")
    lead = state.get("lead", {}) or {}
    company = lead.get("company") or "the prospect's company"
    domain = lead.get("domain") or ""
    title = lead.get("title") or "decision maker"
    try:
        result = await llm.complete(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a B2B sales research assistant. Produce 2-3 "
                        "concise bullet points: industry, likely pain points, "
                        "and a relevant trigger event."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Company: {company}\nDomain: {domain}\n"
                        f"Contact title: {title}"
                    ),
                },
            ],
            max_tokens=256,
        )
        state["research_results"] = {
            "summary": result.content,
            "company": company,
            "domain": domain,
        }
        _complete_entry(
            entry,
            details={"summary_chars": len(result.content)},
            llm=result,
        )
    except Exception as exc:  # pragma: no cover — defensive
        logger.exception("research_node failed")
        state["error"] = state.get("error") or f"research_node: {exc}"
        _fail_entry(entry, exc)
    finally:
        _record(state, entry)
    return state


async def enrich_node(state: AgentState, llm: LLMProvider) -> AgentState:
    """Pull supplemental facts about the lead.

    The current implementation is deterministic and offline — it derives a few
    fields from ``lead.domain``. A real adapter (Clearbit/Apollo/Hunter) plugs
    in here.
    """
    state["current_step"] = "enrich"
    entry = _start_entry("enrich")
    lead = state.get("lead", {}) or {}
    domain = (lead.get("domain") or "").lower().strip()
    company = lead.get("company") or ""
    enriched: dict[str, Any] = {}
    if domain:
        enriched["website"] = f"https://{domain}"
        enriched["linkedin_company_url"] = lead.get("linkedin_url") or ""
    if company:
        enriched["company"] = company
    state["enriched_data"] = enriched
    _complete_entry(entry, details={"fields_added": len(enriched)})
    _record(state, entry)
    return state


async def draft_email_node(state: AgentState, llm: LLMProvider) -> AgentState:
    """Generate the outreach email body and subject."""
    state["current_step"] = "draft_email"
    entry = _start_entry("draft_email")
    lead = state.get("lead", {}) or {}
    research = (state.get("research_results") or {}).get("summary", "")
    contact_name = lead.get("name") or "there"
    company = lead.get("company") or "your team"
    try:
        result = await llm.complete(
            [
                {
                    "role": "system",
                    "content": (
                        "You write short, specific outreach emails. Reply with "
                        "two lines:\n"
                        "Subject: <subject>\n"
                        "Body: <body, 4-6 sentences, no fluff>"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Contact: {contact_name}\nCompany: {company}\n"
                        f"Research notes:\n{research}"
                    ),
                },
            ],
            max_tokens=400,
        )
        subject, body = _split_subject_body(result.content)
        state["draft_subject"] = subject
        state["draft_email"] = body
        _complete_entry(
            entry,
            details={"subject": subject, "body_chars": len(body)},
            llm=result,
        )
    except Exception as exc:  # pragma: no cover
        logger.exception("draft_email_node failed")
        state["error"] = state.get("error") or f"draft_email_node: {exc}"
        _fail_entry(entry, exc)
    finally:
        _record(state, entry)
    return state


def _split_subject_body(content: str) -> tuple[str, str]:
    """Best-effort parse of the LLM output into (subject, body).

    Tolerates models that ignore the format request — falls back to using
    the first line as the subject and the rest as the body.
    """
    subject = ""
    body_lines: list[str] = []
    seen_body = False
    for line in content.splitlines():
        stripped = line.strip()
        if not subject and stripped.lower().startswith("subject:"):
            subject = stripped.split(":", 1)[1].strip()
            continue
        if not seen_body and stripped.lower().startswith("body:"):
            after = stripped.split(":", 1)[1].strip()
            if after:
                body_lines.append(after)
            seen_body = True
            continue
        body_lines.append(line)
    if not subject:
        # Fall back: first non-blank line becomes the subject.
        for i, line in enumerate(content.splitlines()):
            if line.strip():
                subject = line.strip()[:100]
                body_lines = content.splitlines()[i + 1 :]
                break
    body = "\n".join(line for line in body_lines).strip()
    return subject or "Quick question", body or content.strip()


async def verify_node(state: AgentState, llm: LLMProvider) -> AgentState:
    """Sanity-check the draft before we declare success."""
    state["current_step"] = "verify"
    entry = _start_entry("verify")
    body = state.get("draft_email", "") or ""
    issues: list[str] = []
    if len(body) < 30:
        issues.append("body_too_short")
    if len(body) > 4000:
        issues.append("body_too_long")
    banned = ("password", "credit card", "ssn")
    if any(token in body.lower() for token in banned):
        issues.append("body_contains_banned_phrase")
    state["verification_result"] = {"issues": issues, "passed": not issues}
    _complete_entry(entry, details={"issues": issues, "body_chars": len(body)})
    _record(state, entry)
    return state


__all__ = [
    "research_node",
    "enrich_node",
    "draft_email_node",
    "verify_node",
]
