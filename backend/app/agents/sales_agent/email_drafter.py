"""
Deterministic email drafting engine.
Uses template-based approach with variable substitution — no AI.
"""
from typing import Dict, Any, Optional
from string import Template


# Email templates by type
TEMPLATES = {
    "research_intro": Template(
        "Subject: $subject\n\n"
        "Hi $first_name,\n\n"
        "I came across $company and was impressed by the work your team "
        "is doing in $industry. "
        "$personalization_line\n\n"
        "I'd love to share how we help companies like yours streamline "
        "their sales outreach process — saving teams an average of "
        "10+ hours per week on prospecting.\n\n"
        "Would you be open to a brief 15-minute call this week?\n\n"
        "Best regards,\n$sender_name"
    ),
    "follow_up": Template(
        "Subject: $subject\n\n"
        "Hi $first_name,\n\n"
        "I wanted to follow up on my previous message. I understand "
        "you're busy — just wanted to make sure this didn't slip "
        "through the cracks.\n\n"
        "$value_prop\n\n"
        "Would $meeting_suggestion work for a quick chat?\n\n"
        "Thanks,\n$sender_name"
    ),
    "cold_outreach": Template(
        "Subject: $subject\n\n"
        "Hi $first_name,\n\n"
        "$opening_line\n\n"
        "At $our_company, we help $target_segment $value_prop.\n\n"
        "$social_proof\n\n"
        "Would you be interested in seeing how this could work for "
        "$company?\n\n"
        "Best,\n$sender_name"
    ),
}


def draft_email(
    template_type: str,
    lead_name: str = "",
    lead_company: str = "",
    lead_title: str = "",
    research_data: Dict[str, Any] = None,
    sender_name: str = "Sales Team",
) -> Dict[str, str]:
    """
    Draft an email using deterministic templates.

    Returns:
        Dict with 'subject' and 'body' keys.
    """
    research_data = research_data or {}

    first_name = lead_name.split(" ")[0] if lead_name else "there"
    company = lead_company or "your company"
    industry = research_data.get("industry", "your space")

    # Build personalization line based on available data
    personalization = _build_personalization(lead_title, research_data)

    # Generate subject line
    subject = _generate_subject(template_type, first_name, company)

    template = TEMPLATES.get(template_type, TEMPLATES["research_intro"])

    # Safe substitution — missing keys become empty strings
    try:
        body = template.safe_substitute(
            subject=subject,
            first_name=first_name,
            company=company,
            industry=industry,
            personalization_line=personalization,
            sender_name=sender_name,
            value_prop=_get_value_prop(research_data),
            meeting_suggestion="Tuesday or Wednesday afternoon",
            opening_line=f"I noticed {company} has been growing rapidly.",
            our_company="our platform",
            target_segment="sales teams",
            social_proof="Companies using our platform see 3x more qualified meetings.",
        )
    except Exception:
        body = f"Hi {first_name},\n\nI'd love to connect about how we can help {company}.\n\nBest,\n{sender_name}"

    return {
        "subject": subject,
        "body": body,
    }


def _generate_subject(template_type: str, first_name: str, company: str) -> str:
    """Generate appropriate subject line."""
    subjects = {
        "research_intro": f"Quick question for {first_name} at {company}",
        "follow_up": f"Following up — {company}",
        "cold_outreach": f"Idea for {company}",
    }
    return subjects.get(template_type, f"Introduction — {company}")


def _build_personalization(title: str, research_data: Dict[str, Any]) -> str:
    """Build a personalization line from available data."""
    lines = []

    if research_data.get("employee_count"):
        count = research_data["employee_count"]
        if count > 500:
            lines.append("As a larger organization, I imagine managing your sales pipeline at scale is a priority.")
        elif count > 50:
            lines.append("For a growing team like yours, efficient outreach can be a game-changer.")

    if title:
        title_lower = title.lower()
        if any(t in title_lower for t in ("ceo", "founder", "owner")):
            lines.append("As a founder, I know your time is incredibly valuable.")
        elif any(t in title_lower for t in ("vp sales", "head of sales", "sales director")):
            lines.append("In your role leading sales, I imagine pipeline quality is top of mind.")

    return lines[0] if lines else ""


def _get_value_prop(research_data: Dict[str, Any]) -> str:
    """Get appropriate value proposition based on research."""
    employee_count = research_data.get("employee_count", 0)
    if employee_count > 200:
        return "Our platform helps enterprise teams automate prospecting while maintaining personalization at scale."
    else:
        return "We help growing teams book more qualified meetings without adding headcount."
