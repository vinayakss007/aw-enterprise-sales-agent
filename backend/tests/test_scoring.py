"""Tests for the deterministic lead scoring engine."""
import pytest
from app.agents.sales_agent.scoring import score_lead, get_score_label, _is_decision_maker


class TestScoreLead:
    def test_empty_lead_scores_zero(self):
        score = score_lead()
        assert score == 0

    def test_business_email_adds_points(self):
        score = score_lead(email="john@acme.com")
        assert score >= 15  # has_business_email

    def test_free_email_no_business_points(self):
        score = score_lead(email="john@gmail.com")
        assert score == 0  # gmail is free

    def test_complete_lead_scores_high(self):
        score = score_lead(
            email="ceo@bigcorp.com",
            company="Big Corp",
            title="CEO",
            linkedin_url="https://linkedin.com/in/ceo",
            phone="+1555123456",
            research_data={"employee_count": 500, "source": "clearbit"},
        )
        assert score >= 80

    def test_company_adds_points(self):
        base = score_lead(email="a@corp.com")
        with_company = score_lead(email="a@corp.com", company="Corp Inc")
        assert with_company > base

    def test_title_adds_points(self):
        base = score_lead(email="a@corp.com")
        with_title = score_lead(email="a@corp.com", title="Engineer")
        assert with_title > base

    def test_decision_maker_title_high_score(self):
        regular = score_lead(email="a@corp.com", title="Engineer")
        dm = score_lead(email="a@corp.com", title="VP of Sales")
        assert dm > regular

    def test_score_capped_at_100(self):
        score = score_lead(
            email="ceo@huge.com",
            company="Huge Inc",
            title="CEO and Founder",
            linkedin_url="url",
            phone="123",
            research_data={"employee_count": 10000, "source": "clearbit"},
        )
        assert score <= 100


class TestGetScoreLabel:
    def test_hot(self):
        assert get_score_label(80) == "hot"
        assert get_score_label(100) == "hot"

    def test_warm(self):
        assert get_score_label(60) == "warm"
        assert get_score_label(79) == "warm"

    def test_cool(self):
        assert get_score_label(40) == "cool"
        assert get_score_label(59) == "cool"

    def test_cold(self):
        assert get_score_label(0) == "cold"
        assert get_score_label(39) == "cold"


class TestIsDecisionMaker:
    def test_ceo(self):
        assert _is_decision_maker("CEO") is True

    def test_vp(self):
        assert _is_decision_maker("VP of Engineering") is True

    def test_director(self):
        assert _is_decision_maker("Director of Sales") is True

    def test_regular_employee(self):
        assert _is_decision_maker("Software Engineer") is False

    def test_case_insensitive(self):
        assert _is_decision_maker("chief technology officer") is True
