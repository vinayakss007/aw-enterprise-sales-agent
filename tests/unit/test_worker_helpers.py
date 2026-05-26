"""Pure-function unit tests for the campaign worker helpers."""
from __future__ import annotations

from types import SimpleNamespace


def _fake_lead(**overrides):
    base = {
        "name": "Pat Patterson",
        "company": "Target Inc",
        "email": "pat@target.test",
        "domain": "target.test",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_render_template_substitutes_known_tokens():
    from app.workers.campaigns import render_template

    out = render_template(
        "Hi {{first_name}}, saw {{company}} is hiring.", _fake_lead()
    )
    assert out == "Hi Pat, saw Target Inc is hiring."


def test_render_template_is_case_insensitive_on_token_names():
    from app.workers.campaigns import render_template

    out = render_template("{{NAME}} <{{Email}}>", _fake_lead())
    assert out == "Pat Patterson <pat@target.test>"


def test_render_template_leaves_unknown_tokens_alone():
    from app.workers.campaigns import render_template

    out = render_template("Hi {{unknown_field}} from {{company}}", _fake_lead())
    # Unknown tokens are visible (not silently dropped) so typos surface.
    assert "{{unknown_field}}" in out
    assert "Target Inc" in out


def test_render_template_handles_missing_lead_fields():
    from app.workers.campaigns import render_template

    lead = _fake_lead(name=None, company="")
    out = render_template("hi {{first_name}} of {{company}}!", lead)
    assert out == "hi  of !"  # empties for missing fields, no crash


def test_render_template_returns_empty_for_empty_input():
    from app.workers.campaigns import render_template

    assert render_template("", _fake_lead()) == ""
    assert render_template(None, _fake_lead()) is None  # type: ignore[arg-type]


def test_worker_stats_as_dict_round_trips():
    from app.workers.campaigns import WorkerStats

    stats = WorkerStats()
    stats.processed = 3
    stats.advanced = 1
    stats.completed = 1
    stats.failed = 1
    stats.emails_sent = 2
    stats.errors.append("a/b: boom")
    payload = stats.as_dict()
    assert payload == {
        "processed": 3,
        "advanced": 1,
        "completed": 1,
        "failed": 1,
        "skipped": 0,
        "emails_sent": 2,
        "errors": ["a/b: boom"],
    }


def test_cli_parses_campaigns_subcommand():
    from app.workers.__main__ import _build_parser

    parser = _build_parser()
    args = parser.parse_args(
        ["campaigns", "--once", "--tenant", "t-123", "--interval", "5"]
    )
    assert args.worker == "campaigns"
    assert args.once is True
    assert args.tenant == "t-123"
    assert args.interval == 5.0
