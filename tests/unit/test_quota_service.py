"""Quota service unit tests (no DB)."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest


def _fake_user(tenant_id="t1"):
    from types import SimpleNamespace
    return SimpleNamespace(id="u1", tenant_id=tenant_id)


def test_default_limits_loaded_when_tenant_has_no_overrides():
    from app.services.quota_service import DEFAULT_LIMITS, QuotaService

    db = MagicMock()
    # Simulate tenant with no limits set.
    fake_tenant = MagicMock()
    fake_tenant.limits = None
    db.query.return_value.filter.return_value.first.return_value = fake_tenant

    service = QuotaService(db, _fake_user())
    assert service.limits == DEFAULT_LIMITS


def test_tenant_overrides_merge_with_defaults():
    from app.services.quota_service import DEFAULT_LIMITS, QuotaService

    db = MagicMock()
    fake_tenant = MagicMock()
    fake_tenant.limits = {"max_leads": 10}
    db.query.return_value.filter.return_value.first.return_value = fake_tenant

    service = QuotaService(db, _fake_user())
    assert service.limits["max_leads"] == 10
    # Other defaults still present.
    assert service.limits["max_campaigns"] == DEFAULT_LIMITS["max_campaigns"]


def test_check_lead_create_raises_429_when_over_limit():
    from fastapi import HTTPException

    from app.services.quota_service import QuotaService

    db = MagicMock()
    fake_tenant = MagicMock()
    fake_tenant.limits = {"max_leads": 5}
    db.query.return_value.filter.return_value.first.return_value = fake_tenant
    # First call loads tenant, second call counts leads.
    db.query.return_value.filter.return_value.scalar.return_value = 5

    service = QuotaService(db, _fake_user())
    # Force limits to be loaded.
    service._limits = {"max_leads": 5}

    with pytest.raises(HTTPException) as exc_info:
        service.check_lead_create()
    assert exc_info.value.status_code == 429
    assert "leads" in exc_info.value.detail


def test_check_lead_create_passes_when_under_limit():
    from app.services.quota_service import QuotaService

    db = MagicMock()
    db.query.return_value.filter.return_value.scalar.return_value = 3

    service = QuotaService(db, _fake_user())
    service._limits = {"max_leads": 5}
    # Should not raise.
    service.check_lead_create()


def test_get_usage_summary_returns_current_and_limits():
    from app.services.quota_service import QuotaService

    db = MagicMock()
    db.query.return_value.filter.return_value.scalar.return_value = 7

    service = QuotaService(db, _fake_user())
    service._limits = {"max_leads": 100, "max_campaigns": 50, "max_kb_entries": 200, "max_agent_runs_per_day": 100}

    summary = service.get_usage_summary()
    assert summary["leads"]["current"] == 7
    assert summary["leads"]["limit"] == 100
