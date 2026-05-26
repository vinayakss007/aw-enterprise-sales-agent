"""
Deterministic lead research module.
Uses public web APIs and domain lookups to gather company/contact info.
No AI dependency — all logic is rule-based.
"""
import logging
from typing import Dict, Any, Optional
import httpx
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


async def research_company(domain: str) -> Dict[str, Any]:
    """
    Research a company by its domain using public sources.
    Returns structured company information.
    """
    results: Dict[str, Any] = {
        "domain": domain,
        "source": "domain_lookup",
    }

    # Try to get basic info from the domain itself
    if domain:
        results["website"] = f"https://{domain}"
        # Extract likely company name from domain
        parts = domain.split(".")
        if len(parts) >= 2:
            results["inferred_name"] = parts[0].replace("-", " ").title()

    # Try clearbit-style enrichment if available
    clearbit_data = await _try_clearbit_enrichment(domain)
    if clearbit_data:
        results.update(clearbit_data)
        results["source"] = "clearbit"

    return results


async def research_contact(email: str, name: str = "") -> Dict[str, Any]:
    """
    Research a contact by email.
    Returns structured contact information.
    """
    results: Dict[str, Any] = {
        "email": email,
        "email_valid": _validate_email_format(email),
    }

    if email:
        domain = email.split("@")[-1] if "@" in email else ""
        results["domain"] = domain
        results["is_business_email"] = not _is_free_email(domain)

    if name:
        parts = name.strip().split(" ", 1)
        results["first_name"] = parts[0]
        results["last_name"] = parts[1] if len(parts) > 1 else ""

    return results


async def _try_clearbit_enrichment(domain: str) -> Optional[Dict[str, Any]]:
    """
    Try Clearbit company enrichment API.
    Returns None if API key not configured or request fails.
    """
    from app.core.config import settings

    if not settings.CLEARBIT_API_KEY:
        return None

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://company.clearbit.com/v2/companies/find?domain={domain}",
                headers={"Authorization": f"Bearer {settings.CLEARBIT_API_KEY}"},
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    "company_name": data.get("name", ""),
                    "industry": data.get("category", {}).get("industry", ""),
                    "employee_count": data.get("metrics", {}).get("employees", 0),
                    "annual_revenue": data.get("metrics", {}).get("annualRevenue", ""),
                    "description": data.get("description", ""),
                    "location": data.get("geo", {}).get("city", ""),
                    "tech_stack": data.get("tech", []),
                }
    except Exception as e:
        logger.warning(f"Clearbit enrichment failed for {domain}: {e}")

    return None


def _validate_email_format(email: str) -> bool:
    """Basic email format validation."""
    if not email or "@" not in email:
        return False
    local, domain = email.rsplit("@", 1)
    return len(local) > 0 and "." in domain and len(domain) > 2


FREE_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "aol.com", "icloud.com", "mail.com", "protonmail.com",
    "zoho.com", "yandex.com", "gmx.com", "live.com",
}


def _is_free_email(domain: str) -> bool:
    """Check if the email domain is a free email provider."""
    return domain.lower() in FREE_EMAIL_DOMAINS
