"""Tests for the deterministic email drafting engine."""
import pytest
from app.agents.sales_agent.email_drafter import draft_email, _generate_subject


class TestDraftEmail:
    def test_research_intro_template(self):
        result = draft_email(
            template_type="research_intro",
            lead_name="Jane Doe",
            lead_company="Acme Corp",
            sender_name="Bob",
        )
        assert "subject" in result
        assert "body" in result
        assert "Jane" in result["body"]
        assert "Acme Corp" in result["body"]
        assert "Bob" in result["body"]

    def test_follow_up_template(self):
        result = draft_email(
            template_type="follow_up",
            lead_name="John Smith",
            lead_company="BigCo",
        )
        assert "follow up" in result["body"].lower()

    def test_cold_outreach_template(self):
        result = draft_email(
            template_type="cold_outreach",
            lead_name="Alice",
            lead_company="StartupX",
        )
        assert "Alice" in result["body"]

    def test_unknown_template_falls_back(self):
        result = draft_email(
            template_type="nonexistent",
            lead_name="Test",
        )
        assert "subject" in result
        assert "body" in result

    def test_empty_lead_name_uses_fallback(self):
        result = draft_email(template_type="research_intro", lead_name="")
        assert "there" in result["body"]  # fallback greeting

    def test_personalization_for_large_company(self):
        result = draft_email(
            template_type="research_intro",
            lead_name="CEO Person",
            lead_company="Big Corp",
            lead_title="CEO",
            research_data={"employee_count": 1000},
        )
        assert "larger organization" in result["body"] or "founder" in result["body"].lower()

    def test_subject_includes_company(self):
        result = draft_email(
            template_type="research_intro",
            lead_name="Jane",
            lead_company="TechCo",
        )
        assert "TechCo" in result["subject"]


class TestGenerateSubject:
    def test_research_intro_subject(self):
        subject = _generate_subject("research_intro", "Jane", "Acme")
        assert "Jane" in subject
        assert "Acme" in subject

    def test_follow_up_subject(self):
        subject = _generate_subject("follow_up", "John", "BigCo")
        assert "BigCo" in subject
