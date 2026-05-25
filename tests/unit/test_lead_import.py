"""Unit tests for the CSV import + export helpers (no DB)."""
from __future__ import annotations

from types import SimpleNamespace


def _fake_lead(**overrides):
    base = {
        "email": "lead@target.test",
        "name": "Pat Patterson",
        "company": "Target Inc",
        "domain": "target.test",
        "title": "CEO",
        "linkedin_url": "https://linkedin.com/in/pat",
        "phone": "+1-555-0100",
        "status": "new",
        "source": "agent",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_export_emits_canonical_header_and_rows():
    from app.services.customer.lead_import import CSV_FIELDS, export_leads_csv

    csv_text = export_leads_csv([_fake_lead(), _fake_lead(email="b@target.test")])
    lines = csv_text.strip().splitlines()
    assert lines[0].split(",") == list(CSV_FIELDS)
    assert lines[1].startswith("lead@target.test")
    assert lines[2].startswith("b@target.test")


def test_export_handles_missing_fields():
    """Leads with None fields should produce empty cells, not the literal None."""
    from app.services.customer.lead_import import export_leads_csv

    sparse = SimpleNamespace(
        email=None, name="X", company=None, domain=None, title=None,
        linkedin_url=None, phone=None, status="new", source=None,
    )
    csv_text = export_leads_csv([sparse])
    line = csv_text.strip().splitlines()[1]
    assert "None" not in line
    # Row layout: email,name,company,domain,title,linkedin_url,phone,status,source
    assert line == ",X,,,,,,new,"
