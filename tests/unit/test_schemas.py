"""Schema validation behaviour."""
from __future__ import annotations

import pytest


def test_user_create_requires_password():
    from pydantic import ValidationError

    from app.schemas.user import UserCreate

    with pytest.raises(ValidationError):
        UserCreate(email="alice@example.com", name="Alice")  # type: ignore[call-arg]


def test_user_create_validates_email():
    from pydantic import ValidationError

    from app.schemas.user import UserCreate

    with pytest.raises(ValidationError):
        UserCreate(email="not-an-email", name="Alice", password="hunter2")


def test_lead_create_minimal_payload_accepted():
    from app.schemas.lead import LeadCreate

    lead = LeadCreate(email="lead@example.com", name="Lead Person")
    assert lead.email == "lead@example.com"
    assert lead.source == "agent"  # default


def test_campaign_step_type_enum():
    from app.schemas.campaign import CampaignStep, CampaignStepType

    step = CampaignStep(
        order=1, type="email", title="Intro", content="hello", delay_days=0
    )
    assert step.type is CampaignStepType.email
