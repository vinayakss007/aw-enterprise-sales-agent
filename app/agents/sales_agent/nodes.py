"""Agent nodes.

Each node:
  * is an ``async`` function ``(state, ctx) -> state`` where ``ctx`` is an
    ``AgentContext`` bundling the LLM + optional tools (search, knowledge).
  * mutates the supplied state in-place (and returns it for chaining).
  * appends a structured ``TrajectoryEntry`` describing what happened.
  * never raises through to the caller — it sets ``state['error']`` instead so
    the orchestrator can decide how to handle it.

The shape is compatible with LangGraph nodes and can be dropped into a
LangGraph ``StateGraph`` later without changing the function signatures.
"""
from __future__ import annotations

import logging
import time
from typing import Any

from app.agents.sales_agent.context import AgentContext
from app.agents.sales_agent.llm import LLMResult
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


def _skip_entry(entry: TrajectoryEntry, reason: str) -> TrajectoryEntry:
    entry["status"] = "skipped"
    entry["completed_at"] = time.time()
    entry["duration_ms"] = int((entry["completed_at"] - entry["started_at"]) * 1000)
    entry["details"] = {"reason": reason}
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


async def research_node(state: AgentState, ctx: AgentContext) -> AgentState:
    """Gather a brief profile of the target company.

    When a ``SearchProvider`` is available on the context, the node fetches
    the top results for "{company} news" and feeds the snippets to the LLM
    as grounding. Without one, this falls back to a pure-LLM summary.
    """
    state["current_step"] = "research"
    entry = _start_entry("research")
    lead = state.get("lead", {}) or {}
    company = lead.get("company") or "the prospect's company"
    domain = lead.get("domain") or ""
    title = lead.get("title") or "decision maker"

    search_block = ""
    search_results: list[dict[str, Any]] = []
    if ctx.search is not None and (lead.get("company") or domain):
        try:
            query = f"{company} {domain}".strip()
            hits = await ctx.search.search(query, limit=4)
            search_results = [hit.to_dict() for hit in hits]
            if hits:
                search_block = "\n\nRecent web results:\n" + "\n".join(
                    f"- {h.title} ({h.url}): {h.snippet}" for h in hits
                )
        except Exception as exc:  # pragma: no cover - tool failures shouldn't kill the run
            logger.warning("research_node: search failed: %s", exc)

    try:
        result = await ctx.llm.complete(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a B2B sales research assistant. Produce 2-3 "
                        "concise bullet points: industry, likely pain points, "
                        "and a relevant trigger event. Cite a search result "
                        "URL where it strengthens a claim."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Company: {company}\nDomain: {domain}\n"
                        f"Contact title: {title}{search_block}"
                    ),
                },
            ],
            max_tokens=320,
        )
        state["research_results"] = {
            "summary": result.content,
            "company": company,
            "domain": domain,
            "search": search_results,
        }
        _complete_entry(
            entry,
            details={
                "summary_chars": len(result.content),
                "search_results": len(search_results),
                "search_provider": getattr(ctx.search, "provider", None) if ctx.search else None,
            },
            llm=result,
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("research_node failed")
        state["error"] = state.get("error") or f"research_node: {exc}"
        _fail_entry(entry, exc)
    finally:
        _record(state, entry)
    return state


async def enrich_node(state: AgentState, ctx: AgentContext) -> AgentState:
    """Pull supplemental facts about the lead.

    Today this derives a few fields from ``lead.domain``. The full
    ``EnrichmentService`` (Clearbit etc.) lives at the customer-service
    layer and is invoked from the leads endpoint, not from the agent
    pipeline — keeps the agent free of DB calls.
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


async def knowledge_node(state: AgentState, ctx: AgentContext) -> AgentState:
    """Retrieve relevant knowledge-base entries for the prospect.

    Skips cleanly when no ``KnowledgeLookup`` is wired into the context,
    so test runs without a DB never crash here. Results land in
    ``state['knowledge_results']`` as a list of dicts so the
    ``draft_email`` node can include them in the prompt.
    """
    state["current_step"] = "knowledge"
    entry = _start_entry("knowledge")
    if ctx.knowledge is None or not ctx.tenant_id:
        _skip_entry(entry, "no knowledge provider configured")
        _record(state, entry)
        return state

    lead = state.get("lead", {}) or {}
    parts = [lead.get("company") or "", lead.get("title") or "", lead.get("domain") or ""]
    query = " ".join(p for p in parts if p).strip()
    if not query:
        _skip_entry(entry, "empty query")
        _record(state, entry)
        return state

    try:
        matches = await ctx.knowledge.lookup(
            query, tenant_id=str(ctx.tenant_id), limit=3
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("knowledge_node lookup failed: %s", exc)
        _fail_entry(entry, exc)
        _record(state, entry)
        return state

    state["knowledge_results"] = [
        {
            "id": m.id,
            "title": m.title,
            "content": m.content,
            "category": m.category,
            "tags": m.tags,
            "score": m.score,
        }
        for m in matches
    ]
    _complete_entry(
        entry, details={"matches": len(matches), "query_chars": len(query)}
    )
    _record(state, entry)
    return state


async def draft_email_node(state: AgentState, ctx: AgentContext) -> AgentState:
    """Generate the outreach email body and subject."""
    state["current_step"] = "draft_email"
    entry = _start_entry("draft_email")
    lead = state.get("lead", {}) or {}
    research = (state.get("research_results") or {}).get("summary", "")
    contact_name = lead.get("name") or "there"
    company = lead.get("company") or "your team"

    knowledge = state.get("knowledge_results") or []
    knowledge_block = ""
    if knowledge:
        knowledge_block = "\n\nRelevant talking points from the knowledge base:\n" + "\n".join(
            f"- {m['title']}: {m['content'][:240]}" for m in knowledge[:3]
        )

    try:
        result = await ctx.llm.complete(
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
                        f"Research notes:\n{research}{knowledge_block}"
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
            details={
                "subject": subject,
                "body_chars": len(body),
                "knowledge_used": len(knowledge),
            },
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


async def verify_node(state: AgentState, ctx: AgentContext) -> AgentState:
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
    "knowledge_node",
    "draft_email_node",
    "verify_node",
]
