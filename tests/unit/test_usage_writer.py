"""Usage writer unit tests."""
from __future__ import annotations

from unittest.mock import MagicMock


def test_record_usage_creates_row_and_commits():
    from app.services.usage_writer import record_usage

    db = MagicMock()
    row = record_usage(
        db,
        tenant_id="t1",
        user_id="u1",
        metric_type="agent_run",
        value=1200,
        cost_cents=15,
        resource_id="exec-1",
    )
    db.add.assert_called_once()
    db.commit.assert_called_once()
    assert row.metric_type == "agent_run"
    assert row.value == 1200
    assert row.cost_cents == 15


def test_record_usage_skips_commit_when_flag_false():
    from app.services.usage_writer import record_usage

    db = MagicMock()
    record_usage(
        db,
        tenant_id="t1",
        metric_type="lead_create",
        commit=False,
    )
    db.add.assert_called_once()
    db.commit.assert_not_called()
