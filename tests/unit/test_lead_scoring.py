"""Unit tests for the deterministic lead scoring function."""
from __future__ import annotations

from app.services.customer.lead_scoring import compute_lead_score


def test_no_enrichment_data_returns_default_30():
    assert compute_lead_score(None) == 30
    assert compute_lead_score({}) == 30


def test_software_industry_adds_20():
    score = compute_lead_score({"industry": "Software"})
    assert score == 20


def test_employee_count_over_1000_adds_25():
    score = compute_lead_score({"employee_count": 1500})
    assert score == 25


def test_annual_revenue_over_50m_adds_25():
    score = compute_lead_score({"annual_revenue": 60_000_000})
    assert score == 25


def test_max_score_capped_at_100():
    # All flags active — industry(20) + employees(25) + revenue(25) +
    # linkedin(10) + website(5) + confidence(10) = 95; should stay <= 100.
    data = {
        "industry": "Healthcare",
        "employee_count": 5000,
        "annual_revenue": 100_000_000,
        "linkedin_url": "https://linkedin.com/in/someone",
        "website": "https://example.com",
        "confidence": 0.9,
    }
    score = compute_lead_score(data)
    assert score <= 100
    assert score == 95  # exact expected value


def test_linkedin_url_adds_10():
    score = compute_lead_score({"linkedin_url": "https://linkedin.com/in/someone"})
    assert score == 10


def test_confidence_over_05_adds_10():
    score = compute_lead_score({"confidence": 0.8})
    assert score == 10
