"""
Deterministic lead scoring engine.
Assigns a 0-100 score based on weighted rules — no AI.
"""
from typing import Dict, Any


# Scoring weights (all add up to max 100)
SCORING_RULES = {
    "has_business_email": 15,
    "has_company": 10,
    "has_title": 10,
    "has_linkedin": 5,
    "has_phone": 5,
    "company_has_employees": 15,  # Has employee count data
    "title_is_decision_maker": 20,
    "industry_match": 10,
    "domain_enriched": 10,
}

DECISION_MAKER_TITLES = {
    "ceo", "cto", "cfo", "coo", "cmo", "cro",
    "vp", "vice president", "director", "head of",
    "founder", "co-founder", "owner", "partner",
    "president", "chief", "svp", "evp",
}


def score_lead(
    email: str = "",
    company: str = "",
    title: str = "",
    linkedin_url: str = "",
    phone: str = "",
    research_data: Dict[str, Any] = None,
) -> int:
    """
    Score a lead from 0-100 based on data completeness and signals.
    Purely deterministic — rules engine, no ML.
    """
    research_data = research_data or {}
    score = 0

    # Has business email (not gmail, etc.)
    if email and "@" in email:
        domain = email.split("@")[-1]
        from app.agents.sales_agent.research import _is_free_email
        if not _is_free_email(domain):
            score += SCORING_RULES["has_business_email"]

    # Has company
    if company:
        score += SCORING_RULES["has_company"]

    # Has title
    if title:
        score += SCORING_RULES["has_title"]

    # Has LinkedIn
    if linkedin_url:
        score += SCORING_RULES["has_linkedin"]

    # Has phone
    if phone:
        score += SCORING_RULES["has_phone"]

    # Company has employee data from enrichment
    if research_data.get("employee_count", 0) > 0:
        score += SCORING_RULES["company_has_employees"]

    # Title indicates decision maker
    if title and _is_decision_maker(title):
        score += SCORING_RULES["title_is_decision_maker"]

    # Domain was successfully enriched
    if research_data.get("source") not in (None, "domain_lookup"):
        score += SCORING_RULES["domain_enriched"]

    return min(score, 100)


def _is_decision_maker(title: str) -> bool:
    """Check if the title suggests a decision-making role."""
    title_lower = title.lower()
    return any(dm_title in title_lower for dm_title in DECISION_MAKER_TITLES)


def get_score_label(score: int) -> str:
    """Get human-readable label for a score."""
    if score >= 80:
        return "hot"
    elif score >= 60:
        return "warm"
    elif score >= 40:
        return "cool"
    else:
        return "cold"
