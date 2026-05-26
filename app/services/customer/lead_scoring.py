"""Lead scoring service.

Deterministic scoring based on enriched_data fields. Returns a score 0-100
that quantifies how well a lead matches the ideal customer profile.

Scoring breakdown:
  - Industry match (Software/Financial Services/Healthcare): +20
  - Employee count > 200: +15, > 1000: +25 (not cumulative)
  - Annual revenue > 5M: +15, > 50M: +25 (not cumulative)
  - Has linkedin_url: +10
  - Has website: +5
  - Confidence > 0.5: +10
  - Default score with no enriched data: 30
"""
from __future__ import annotations

from typing import Any

# Industries that score highly for B2B SaaS sales targeting.
TARGET_VERTICALS: set[str] = {"software", "financial services", "healthcare"}


def compute_lead_score(enriched_data: dict[str, Any] | None) -> int:
    """Compute a deterministic lead score (0-100) from enriched_data.

    Returns 30 when enriched_data is None or empty.
    """
    if not enriched_data:
        return 30

    score = 0

    # Industry match
    industry = (enriched_data.get("industry") or "").strip().lower()
    if industry in TARGET_VERTICALS:
        score += 20

    # Employee count
    try:
        employee_count = int(enriched_data.get("employee_count", 0))
    except (TypeError, ValueError):
        employee_count = 0
    if employee_count > 1000:
        score += 25
    elif employee_count > 200:
        score += 15

    # Annual revenue (stored as numeric, e.g. 5_000_000)
    try:
        annual_revenue = float(enriched_data.get("annual_revenue", 0))
    except (TypeError, ValueError):
        annual_revenue = 0.0
    if annual_revenue > 50_000_000:
        score += 25
    elif annual_revenue > 5_000_000:
        score += 15

    # Has linkedin_url
    if enriched_data.get("linkedin_url"):
        score += 10

    # Has website
    if enriched_data.get("website"):
        score += 5

    # Confidence score from enrichment provider
    try:
        confidence = float(enriched_data.get("confidence", 0))
    except (TypeError, ValueError):
        confidence = 0.0
    if confidence > 0.5:
        score += 10

    # Clamp to 0-100
    return max(0, min(100, score))


__all__ = ["compute_lead_score", "TARGET_VERTICALS"]
