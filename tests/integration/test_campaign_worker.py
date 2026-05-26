"""End-to-end campaign worker tests against a real Postgres."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pytest

# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture()
def tenant_and_user(db_session):
    """Create a tenant + owner user and return them."""
    import uuid

    from app.db.models.tenant import Tenant
    from app.db.models.user import User
    from app.services.auth.jwt import get_password_hash

    tenant = Tenant(id=uuid.uuid4(), name="Acme")
    db_session.add(tenant)
    db_session.flush()
    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email="owner@acme.test",
        name="Owner",
        hashed_password=get_password_hash("hunter22"),
        role="owner",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    return tenant, user


@pytest.fixture()
def lead_factory(db_session):
    """Create as many leads as needed against a given tenant/user."""
    import uuid

    from app.db.models.lead import Lead

    def _make(tenant_id, user_id, **overrides) -> Lead:
        lead = Lead(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            email=overrides.pop("email", "lead@target.test"),
            name=overrides.pop("name", "Lead Person"),
            company=overrides.pop("company", "Target Inc"),
            domain=overrides.pop("domain", "target.test"),
        )
        for field, value in overrides.items():
            setattr(lead, field, value)
        db_session.add(lead)
        db_session.commit()
        return lead

    return _make


def _make_campaign(db_session, tenant, user, steps_payload: list[dict[str, Any]]):
    """Helper: create a Campaign + steps in ``draft`` state."""
    import uuid

    from app.db.models.campaign import Campaign, CampaignStep

    campaign = Campaign(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        name="Outreach 1",
        status="draft",
        created_by=user.id,
    )
    db_session.add(campaign)
    db_session.flush()
    for s in steps_payload:
        db_session.add(
            CampaignStep(
                id=uuid.uuid4(),
                campaign_id=campaign.id,
                order=s["order"],
                type=s.get("type", "email"),
                title=s.get("title", "Step"),
                content=s.get("content", "Hello {{first_name}}"),
                delay_days=s.get("delay_days", 0),
                subject=s.get("subject", "Quick hello"),
            )
        )
    db_session.commit()
    return campaign


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_worker_skips_draft_campaigns(db_session, tenant_and_user, lead_factory):
    """Draft campaigns must never fire even if assignments are due."""
    import uuid

    from app.db.models.campaign import CampaignAssignment
    from app.integrations.email.console import ConsoleEmailSender
    from app.workers.campaigns import CampaignWorker

    tenant, user = tenant_and_user
    campaign = _make_campaign(
        db_session, tenant, user, [{"order": 1, "type": "email"}]
    )
    # campaign is in draft — assignment is due immediately.
    lead = lead_factory(tenant.id, user.id)
    db_session.add(
        CampaignAssignment(
            id=uuid.uuid4(),
            campaign_id=campaign.id,
            lead_id=lead.id,
            status="pending",
            next_action_date=datetime.utcnow() - timedelta(minutes=1),
        )
    )
    db_session.commit()

    sender = ConsoleEmailSender()
    worker = CampaignWorker(db_session, email_sender=sender)
    stats = await worker.process_due_assignments()

    assert stats.processed == 0
    assert stats.emails_sent == 0
    assert sender.sent == []


@pytest.mark.asyncio
async def test_single_step_campaign_completes_in_one_tick(
    db_session, tenant_and_user, lead_factory
):
    import uuid

    from app.db.models.campaign import CampaignAssignment
    from app.integrations.email.console import ConsoleEmailSender
    from app.workers.campaigns import CampaignWorker

    tenant, user = tenant_and_user
    campaign = _make_campaign(
        db_session,
        tenant,
        user,
        [
            {
                "order": 1,
                "type": "email",
                "subject": "Hi {{first_name}}",
                "content": "Hello {{first_name}} from {{company}}",
            }
        ],
    )
    campaign.status = "active"
    db_session.commit()

    lead = lead_factory(tenant.id, user.id, name="Pat Patterson", company="Target Inc")
    assignment = CampaignAssignment(
        id=uuid.uuid4(),
        campaign_id=campaign.id,
        lead_id=lead.id,
        status="pending",
        next_action_date=datetime.utcnow() - timedelta(seconds=1),
    )
    db_session.add(assignment)
    db_session.commit()

    sender = ConsoleEmailSender()
    worker = CampaignWorker(db_session, email_sender=sender)
    stats = await worker.process_due_assignments()

    db_session.refresh(assignment)
    assert stats.processed == 1
    assert stats.completed == 1
    assert stats.emails_sent == 1
    assert assignment.status == "completed"
    assert assignment.current_step == 1
    assert assignment.next_action_date is None
    assert len(sender.sent) == 1
    sent = sender.sent[0]
    assert sent.to == "pat@target.test"
    assert sent.subject == "Hi Pat"
    assert "Hello Pat from Target Inc" in sent.body


@pytest.mark.asyncio
async def test_multi_step_campaign_advances_across_ticks(
    db_session, tenant_and_user, lead_factory
):
    import uuid

    from app.db.models.campaign import CampaignAssignment
    from app.integrations.email.console import ConsoleEmailSender
    from app.workers.campaigns import CampaignWorker

    tenant, user = tenant_and_user
    campaign = _make_campaign(
        db_session,
        tenant,
        user,
        [
            {"order": 1, "type": "email", "subject": "Step 1", "content": "Body 1", "delay_days": 0},
            {"order": 2, "type": "email", "subject": "Step 2", "content": "Body 2", "delay_days": 3},
        ],
    )
    campaign.status = "active"
    db_session.commit()

    lead = lead_factory(tenant.id, user.id)
    t0 = datetime(2026, 5, 25, 12, 0, 0)
    assignment = CampaignAssignment(
        id=uuid.uuid4(),
        campaign_id=campaign.id,
        lead_id=lead.id,
        status="pending",
        next_action_date=t0,
    )
    db_session.add(assignment)
    db_session.commit()

    sender = ConsoleEmailSender()

    # Tick 1: only step 1 fires; assignment moves to active with a future
    # next_action_date based on step 2's delay_days.
    worker1 = CampaignWorker(db_session, email_sender=sender, now=t0)
    stats1 = await worker1.process_due_assignments()
    db_session.refresh(assignment)
    assert stats1.advanced == 1
    assert stats1.completed == 0
    assert stats1.emails_sent == 1
    assert assignment.status == "active"
    assert assignment.current_step == 1
    assert assignment.next_action_date == t0 + timedelta(days=3)
    assert sender.sent[-1].subject == "Step 1"

    # Tick 2: still in the future — nothing happens.
    worker_early = CampaignWorker(
        db_session, email_sender=sender, now=t0 + timedelta(days=1)
    )
    stats_early = await worker_early.process_due_assignments()
    db_session.refresh(assignment)
    assert stats_early.processed == 0
    assert assignment.status == "active"
    assert assignment.current_step == 1

    # Tick 3: time has advanced past step 2's due time — completes.
    worker3 = CampaignWorker(
        db_session, email_sender=sender, now=t0 + timedelta(days=3, minutes=1)
    )
    stats3 = await worker3.process_due_assignments()
    db_session.refresh(assignment)
    assert stats3.completed == 1
    assert stats3.emails_sent == 1
    assert assignment.status == "completed"
    assert assignment.current_step == 2
    assert assignment.next_action_date is None
    assert [m.subject for m in sender.sent] == ["Step 1", "Step 2"]


@pytest.mark.asyncio
async def test_step_failure_marks_assignment_failed(
    db_session, tenant_and_user, lead_factory
):
    """If the step raises (e.g. lead has no email), assignment goes to ``failed``."""
    import uuid

    from app.db.models.campaign import CampaignAssignment
    from app.integrations.email.console import ConsoleEmailSender
    from app.workers.campaigns import CampaignWorker

    tenant, user = tenant_and_user
    campaign = _make_campaign(
        db_session, tenant, user, [{"order": 1, "type": "email"}]
    )
    campaign.status = "active"
    db_session.commit()

    lead = lead_factory(tenant.id, user.id, email=None)  # missing email triggers failure
    assignment = CampaignAssignment(
        id=uuid.uuid4(),
        campaign_id=campaign.id,
        lead_id=lead.id,
        status="pending",
        next_action_date=datetime.utcnow() - timedelta(seconds=1),
    )
    db_session.add(assignment)
    db_session.commit()

    worker = CampaignWorker(db_session, email_sender=ConsoleEmailSender())
    stats = await worker.process_due_assignments()
    db_session.refresh(assignment)
    assert stats.failed == 1
    assert stats.emails_sent == 0
    assert assignment.status == "failed"
    assert assignment.current_step == 0
    assert any("no email address" in err for err in stats.errors)


@pytest.mark.asyncio
async def test_call_step_is_recorded_but_does_not_send_email(
    db_session, tenant_and_user, lead_factory
):
    import uuid

    from app.db.models.campaign import CampaignAssignment
    from app.integrations.email.console import ConsoleEmailSender
    from app.workers.campaigns import CampaignWorker

    tenant, user = tenant_and_user
    campaign = _make_campaign(
        db_session,
        tenant,
        user,
        [
            {"order": 1, "type": "call", "subject": "", "content": "ring them"},
            {"order": 2, "type": "email", "subject": "Followup", "content": "Hi"},
        ],
    )
    campaign.status = "active"
    db_session.commit()

    lead = lead_factory(tenant.id, user.id)
    assignment = CampaignAssignment(
        id=uuid.uuid4(),
        campaign_id=campaign.id,
        lead_id=lead.id,
        status="pending",
        next_action_date=datetime.utcnow() - timedelta(seconds=1),
    )
    db_session.add(assignment)
    db_session.commit()

    sender = ConsoleEmailSender()
    worker = CampaignWorker(db_session, email_sender=sender)
    stats = await worker.process_due_assignments()
    db_session.refresh(assignment)
    # Call step advanced but no email was sent.
    assert stats.advanced == 1
    assert stats.emails_sent == 0
    assert sender.sent == []
    assert assignment.status == "active"
    assert assignment.current_step == 1


@pytest.mark.asyncio
async def test_tenant_scoping_isolates_other_tenants(
    db_session, tenant_and_user, lead_factory
):
    import uuid

    from app.db.models.campaign import CampaignAssignment
    from app.db.models.tenant import Tenant
    from app.db.models.user import User
    from app.integrations.email.console import ConsoleEmailSender
    from app.services.auth.jwt import get_password_hash
    from app.workers.campaigns import CampaignWorker

    # Tenant A.
    tenant_a, user_a = tenant_and_user
    campaign_a = _make_campaign(
        db_session,
        tenant_a,
        user_a,
        [{"order": 1, "type": "email", "subject": "A", "content": "A body"}],
    )
    campaign_a.status = "active"
    lead_a = lead_factory(tenant_a.id, user_a.id, email="a@target.test")
    db_session.add(
        CampaignAssignment(
            id=uuid.uuid4(),
            campaign_id=campaign_a.id,
            lead_id=lead_a.id,
            status="pending",
            next_action_date=datetime.utcnow() - timedelta(seconds=1),
        )
    )

    # Tenant B with its own active campaign.
    tenant_b = Tenant(id=uuid.uuid4(), name="OtherCo")
    user_b = User(
        id=uuid.uuid4(),
        tenant_id=tenant_b.id,
        email="b@otherco.test",
        name="B",
        hashed_password=get_password_hash("pw"),
        role="owner",
    )
    db_session.add_all([tenant_b, user_b])
    db_session.flush()
    campaign_b = _make_campaign(
        db_session,
        tenant_b,
        user_b,
        [{"order": 1, "type": "email", "subject": "B", "content": "B body"}],
    )
    campaign_b.status = "active"
    lead_b = lead_factory(tenant_b.id, user_b.id, email="b-lead@target.test")
    db_session.add(
        CampaignAssignment(
            id=uuid.uuid4(),
            campaign_id=campaign_b.id,
            lead_id=lead_b.id,
            status="pending",
            next_action_date=datetime.utcnow() - timedelta(seconds=1),
        )
    )
    db_session.commit()

    sender = ConsoleEmailSender()
    worker = CampaignWorker(db_session, email_sender=sender)
    stats = await worker.process_due_assignments(tenant_id=str(tenant_a.id))

    # Only tenant A's assignment was processed.
    assert stats.processed == 1
    assert stats.emails_sent == 1
    assert {m.to for m in sender.sent} == {"a@target.test"}


@pytest.mark.asyncio
async def test_admin_tick_endpoint(client):
    """The admin tick endpoint must be admin-only and tenant-scoped."""
    # Register a user (becomes owner of a fresh tenant).
    register = client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@acme.test",
            "name": "Admin",
            "password": "hunter22",
        },
    )
    assert register.status_code == 200, register.text
    token_resp = client.post(
        "/api/v1/auth/token",
        data={"username": "admin@acme.test", "password": "hunter22"},
    )
    assert token_resp.status_code == 200
    token = token_resp.json()["access_token"]

    resp = client.post(
        "/api/v1/admin/campaigns/tick",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # No campaigns yet → all counts zero, no errors.
    assert body == {
        "processed": 0,
        "advanced": 0,
        "completed": 0,
        "failed": 0,
        "skipped": 0,
        "emails_sent": 0,
        "agent_runs": 0,
        "errors": [],
    }


@pytest.mark.asyncio
async def test_admin_tick_endpoint_rejects_unauthenticated(client):
    resp = client.post("/api/v1/admin/campaigns/tick")
    assert resp.status_code in (401, 403)



@pytest.mark.asyncio
async def test_agent_mode_step_drafts_with_agent_and_persists_execution(
    db_session, tenant_and_user, lead_factory
):
    """Empty step content triggers SalesAgent + AgentExecution row."""
    import uuid

    from app.db.models.agent_execution import AgentExecution
    from app.db.models.campaign import CampaignAssignment
    from app.integrations.email.console import ConsoleEmailSender
    from app.workers.campaigns import CampaignWorker

    tenant, user = tenant_and_user
    # Empty content → agent mode.
    campaign = _make_campaign(
        db_session,
        tenant,
        user,
        [{"order": 1, "type": "email", "subject": "", "content": ""}],
    )
    campaign.status = "active"
    db_session.commit()

    lead = lead_factory(
        tenant.id, user.id, name="Pat Patterson", company="Target Inc"
    )
    db_session.add(
        CampaignAssignment(
            id=uuid.uuid4(),
            campaign_id=campaign.id,
            lead_id=lead.id,
            status="pending",
            next_action_date=datetime.utcnow() - timedelta(seconds=1),
        )
    )
    db_session.commit()

    sender = ConsoleEmailSender()
    worker = CampaignWorker(db_session, email_sender=sender)
    stats = await worker.process_due_assignments()

    assert stats.processed == 1
    assert stats.completed == 1
    assert stats.emails_sent == 1
    assert stats.agent_runs == 1

    # An AgentExecution row was persisted with the campaign_email type.
    executions = (
        db_session.query(AgentExecution)
        .filter(
            AgentExecution.tenant_id == tenant.id,
            AgentExecution.lead_id == lead.id,
        )
        .all()
    )
    assert len(executions) == 1
    exe = executions[0]
    assert exe.agent_type == "campaign_email"
    assert exe.tokens_input >= 1
    assert exe.tokens_output >= 1
    assert isinstance(exe.trajectory, list)
    assert {entry["step"] for entry in exe.trajectory} >= {
        "research",
        "enrich",
        "draft_email",
        "verify",
    }

    # The email body came from the agent's draft, not a static template.
    assert sender.sent[0].to == "pat@target.test"
    assert len(sender.sent[0].body) >= 30


@pytest.mark.asyncio
async def test_marker_in_content_also_triggers_agent_mode(
    db_session, tenant_and_user, lead_factory
):
    """``[[agent]]`` anywhere in the content flips the step to agent mode."""
    import uuid

    from app.db.models.agent_execution import AgentExecution
    from app.db.models.campaign import CampaignAssignment
    from app.integrations.email.console import ConsoleEmailSender
    from app.workers.campaigns import CampaignWorker

    tenant, user = tenant_and_user
    campaign = _make_campaign(
        db_session,
        tenant,
        user,
        [
            {
                "order": 1,
                "type": "email",
                "subject": "ignored",
                "content": "please [[agent]] write this",
            }
        ],
    )
    campaign.status = "active"
    db_session.commit()

    lead = lead_factory(tenant.id, user.id)
    db_session.add(
        CampaignAssignment(
            id=uuid.uuid4(),
            campaign_id=campaign.id,
            lead_id=lead.id,
            status="pending",
            next_action_date=datetime.utcnow() - timedelta(seconds=1),
        )
    )
    db_session.commit()

    sender = ConsoleEmailSender()
    stats = await CampaignWorker(
        db_session, email_sender=sender
    ).process_due_assignments()

    assert stats.agent_runs == 1
    assert stats.emails_sent == 1
    # The "[[agent]]" marker should NOT appear in the sent body.
    assert "[[agent]]" not in sender.sent[0].body.lower()
    # AgentExecution was persisted.
    assert (
        db_session.query(AgentExecution)
        .filter(AgentExecution.lead_id == lead.id)
        .count()
        == 1
    )
