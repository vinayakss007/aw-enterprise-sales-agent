"""Campaign execution worker.

Walks active campaigns and fires their due steps. Two modes per email step:

* **Template mode** — ``step.content`` is a literal email body with optional
  ``{{name}} / {{first_name}} / {{company}} / ...`` substitutions. This is
  the default and requires no LLM.
* **Agent mode** — ``step.content`` is empty or contains the marker
  ``[[agent]]``. The worker runs the configured ``SalesAgent`` on the lead;
  the agent's drafted subject + body are sent and an ``AgentExecution`` row
  is persisted so token/cost shows up in the user's history.

``call`` and ``task`` steps are recorded but not actioned — manual rep
follow-up. Errors mark the affected ``CampaignAssignment`` as ``failed``;
retry/back-off is left as a follow-up.

The worker is safe to run as ``python -m app.workers campaigns`` (one-shot
or loop) or via ``POST /api/v1/admin/campaigns/tick`` for on-demand
processing in tests and during development.

Concurrency: assumes a single worker process. Add
``SELECT ... FOR UPDATE SKIP LOCKED`` to ``_select_due`` before running
multiple workers in parallel.
"""
from __future__ import annotations

import asyncio
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session, selectinload

from app.agents.sales_agent.graph import SalesAgent
from app.agents.sales_agent.state import AgentState
from app.db.models.agent_execution import AgentExecution
from app.db.models.campaign import Campaign, CampaignAssignment, CampaignStep
from app.db.models.lead import Lead
from app.integrations.email.base import EmailMessage, EmailSender
from app.integrations.email.factory import get_email_sender

logger = logging.getLogger(__name__)


# Marker that flips a step from "template" mode into "agent" mode.
AGENT_MARKER = "[[agent]]"


@dataclass
class WorkerStats:
    """Summary of one ``process_due_assignments`` call."""

    processed: int = 0
    advanced: int = 0
    completed: int = 0
    failed: int = 0
    skipped: int = 0
    emails_sent: int = 0
    agent_runs: int = 0
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "processed": self.processed,
            "advanced": self.advanced,
            "completed": self.completed,
            "failed": self.failed,
            "skipped": self.skipped,
            "emails_sent": self.emails_sent,
            "agent_runs": self.agent_runs,
            "errors": self.errors,
        }


_TEMPLATE_RE = re.compile(r"\{\{\s*([a-zA-Z_]+)\s*\}\}")


def render_template(text: str, lead: Lead) -> str:
    """Replace ``{{name}}`` / ``{{company}}`` etc. with values from the lead.

    Unknown tokens are left untouched so a typo in a template is visible
    rather than silently dropped.
    """
    if not text:
        return text
    name = (lead.name or "").strip()
    first = name.split(" ", 1)[0] if name else ""
    tokens = {
        "name": name,
        "first_name": first,
        "company": lead.company or "",
        "email": lead.email or "",
        "domain": lead.domain or "",
    }

    def _sub(match: re.Match[str]) -> str:
        key = match.group(1).strip().lower()
        return tokens.get(key, match.group(0))

    return _TEMPLATE_RE.sub(_sub, text)


def _is_agent_step(step: CampaignStep) -> bool:
    """A step runs the agent when its content is empty or marked ``[[agent]]``."""
    content = (step.content or "").strip()
    if not content:
        return True
    return AGENT_MARKER in content.lower()


def _lead_to_dict(lead: Lead) -> dict[str, Any]:
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


class CampaignWorker:
    """Drives campaign assignments through their step list."""

    def __init__(
        self,
        db: Session,
        *,
        email_sender: EmailSender | None = None,
        agent: SalesAgent | None = None,
        now: datetime | None = None,
    ) -> None:
        self.db = db
        self.email_sender = email_sender or get_email_sender()
        # Lazy default: agent is only constructed when actually used so
        # template-only campaigns never pay the import cost.
        self._agent_override = agent
        # Allow tests to pin a deterministic clock.
        self._fixed_now = now

    @property
    def agent(self) -> SalesAgent:
        if self._agent_override is not None:
            return self._agent_override
        # Cache so each worker instance shares one agent. Default agent
        # wires search + knowledge so campaign emails benefit from the same
        # grounding the customer-side endpoint provides.
        from app.integrations.search.factory import get_search_provider
        from app.services.customer.knowledge_service import KnowledgeService

        self._agent_override = SalesAgent(
            search=get_search_provider(),
            knowledge=KnowledgeService(self.db),
        )
        return self._agent_override

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    async def process_due_assignments(
        self,
        *,
        tenant_id: str | None = None,
        batch_size: int = 100,
    ) -> WorkerStats:
        """Process up to ``batch_size`` assignments whose next action is due.

        Pass ``tenant_id`` to scope to a single tenant — used by the admin
        tick endpoint so an admin can only fire their own campaigns.
        """
        stats = WorkerStats()
        now = self._fixed_now or datetime.utcnow()
        assignments = self._select_due(now, tenant_id=tenant_id, limit=batch_size)
        for assignment in assignments:
            stats.processed += 1
            try:
                await self._process_one(assignment, now, stats)
            except Exception as exc:  # pragma: no cover — defensive
                logger.exception(
                    "campaign_worker: unhandled error on assignment %s", assignment.id
                )
                stats.failed += 1
                stats.errors.append(f"{assignment.id}: {exc}")
                assignment.status = "failed"
                self.db.commit()
        return stats

    async def run_forever(
        self, *, interval_seconds: float = 30.0, tenant_id: str | None = None
    ) -> None:
        """Process assignments forever, sleeping ``interval_seconds`` between ticks.

        Cancels cleanly on KeyboardInterrupt / asyncio.CancelledError.
        """
        logger.info(
            "campaign_worker: starting loop (interval=%.1fs tenant=%s)",
            interval_seconds,
            tenant_id or "all",
        )
        try:
            while True:
                stats = await self.process_due_assignments(tenant_id=tenant_id)
                logger.info("campaign_worker tick: %s", stats.as_dict())
                await asyncio.sleep(interval_seconds)
        except (asyncio.CancelledError, KeyboardInterrupt):
            logger.info("campaign_worker: loop cancelled, exiting")
            raise

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _select_due(
        self,
        now: datetime,
        *,
        tenant_id: str | None = None,
        limit: int = 100,
    ) -> list[CampaignAssignment]:
        # TODO: when we run >1 worker, switch to
        #       .with_for_update(skip_locked=True)
        query = (
            self.db.query(CampaignAssignment)
            .join(Campaign, CampaignAssignment.campaign_id == Campaign.id)
            .options(selectinload(CampaignAssignment.campaign).selectinload(Campaign.steps))
            .filter(
                Campaign.status == "active",
                CampaignAssignment.status.in_(["pending", "active"]),
                CampaignAssignment.next_action_date != None,  # noqa: E711
                CampaignAssignment.next_action_date <= now,
            )
            .order_by(CampaignAssignment.next_action_date.asc())
            .limit(limit)
        )
        if tenant_id is not None:
            query = query.filter(Campaign.tenant_id == tenant_id)
        return query.all()

    async def _process_one(
        self,
        assignment: CampaignAssignment,
        now: datetime,
        stats: WorkerStats,
    ) -> None:
        steps: list[CampaignStep] = sorted(
            assignment.campaign.steps or [], key=lambda s: s.order
        )
        if not steps:
            stats.skipped += 1
            assignment.status = "completed"
            self.db.commit()
            return

        step_index = assignment.current_step or 0
        if step_index >= len(steps):
            assignment.status = "completed"
            stats.completed += 1
            self.db.commit()
            return

        step = steps[step_index]
        lead = (
            self.db.query(Lead)
            .filter(Lead.id == assignment.lead_id)
            .first()
        )
        if lead is None:
            logger.warning(
                "campaign_worker: lead %s missing for assignment %s",
                assignment.lead_id,
                assignment.id,
            )
            assignment.status = "failed"
            stats.failed += 1
            self.db.commit()
            return

        try:
            await self._execute_step(step, lead, assignment.campaign, stats)
        except Exception as exc:
            logger.warning(
                "campaign_worker: step %s failed for assignment %s: %s",
                step.id,
                assignment.id,
                exc,
            )
            assignment.status = "failed"
            stats.failed += 1
            stats.errors.append(f"{assignment.id}/{step.id}: {exc}")
            self.db.commit()
            return

        # Advance state. Replace (not mutate) the JSONB list so SQLAlchemy
        # picks up the change without needing MutableList configuration.
        completed = list(assignment.completed_steps or [])
        completed.append(str(step.id))
        assignment.completed_steps = completed
        assignment.current_step = step_index + 1
        assignment.updated_at = now

        if assignment.current_step >= len(steps):
            assignment.status = "completed"
            assignment.next_action_date = None
            stats.completed += 1
        else:
            next_step = steps[assignment.current_step]
            assignment.status = "active"
            assignment.next_action_date = now + timedelta(days=next_step.delay_days or 0)
            stats.advanced += 1

        self.db.commit()

    async def _execute_step(
        self,
        step: CampaignStep,
        lead: Lead,
        campaign: Campaign,
        stats: WorkerStats,
    ) -> None:
        step_type = (step.type or "").lower().strip()
        if step_type == "email":
            await self._send_email_step(step, lead, campaign, stats)
            return
        if step_type in ("call", "task"):
            # v1: log only — surfacing as a UI todo is a follow-up.
            logger.info(
                "campaign_worker: %s step %s noted for lead %s",
                step_type,
                step.id,
                lead.id,
            )
            return
        logger.warning(
            "campaign_worker: unknown step type %r on step %s — skipping",
            step.type,
            step.id,
        )

    async def _send_email_step(
        self,
        step: CampaignStep,
        lead: Lead,
        campaign: Campaign,
        stats: WorkerStats,
    ) -> None:
        if not lead.email:
            raise ValueError(f"lead {lead.id} has no email address")

        if _is_agent_step(step):
            subject, body = await self._draft_with_agent(step, lead, campaign, stats)
        else:
            subject = render_template(step.subject or step.title or "", lead)
            body = render_template(step.content or "", lead)

        result = await self.email_sender.send(
            EmailMessage(to=lead.email, subject=subject, body=body)
        )
        if not result.success:
            raise RuntimeError(
                f"email send failed via {result.provider}: {result.error}"
            )
        stats.emails_sent += 1

    async def _draft_with_agent(
        self,
        step: CampaignStep,
        lead: Lead,
        campaign: Campaign,
        stats: WorkerStats,
    ) -> tuple[str, str]:
        """Run the agent for this lead and persist an ``AgentExecution`` row."""
        initial_state: AgentState = {
            "lead": _lead_to_dict(lead),
            "user_id": str(campaign.created_by),
            "tenant_id": str(campaign.tenant_id),
            "agent_type": "campaign_email",
            "current_step": "initialized",
            "trajectory": [],
            "tokens_input": 0,
            "tokens_output": 0,
            "cost_cents": 0,
        }
        started_at = datetime.utcnow()
        result = await self.agent.run(initial_state)
        completed_at = datetime.utcnow()
        stats.agent_runs += 1

        execution = AgentExecution(
            id=uuid.uuid4(),
            tenant_id=campaign.tenant_id,
            user_id=campaign.created_by,
            lead_id=lead.id,
            agent_type="campaign_email",
            trajectory=result.get("trajectory", []),
            success=bool(result.get("success", False)),
            tokens_input=int(result.get("tokens_input", 0)),
            tokens_output=int(result.get("tokens_output", 0)),
            cost_cents=int(result.get("cost_cents", 0)),
            started_at=started_at,
            completed_at=completed_at,
        )
        self.db.add(execution)
        # Caller commits after advancing the assignment so audit + agent row
        # land in the same transaction.

        subject = result.get("draft_subject") or render_template(
            step.subject or step.title or "Quick question", lead
        )
        body = result.get("draft_email") or ""
        if not body:
            raise RuntimeError("agent produced an empty email body")
        return subject, body


__all__ = ["CampaignWorker", "WorkerStats", "render_template", "AGENT_MARKER"]
