"""Unit tests for the worker's agent-mode email step (no DB needed)."""
from __future__ import annotations

from types import SimpleNamespace

import pytest


def test_is_agent_step_marker():
    from app.workers.campaigns import _is_agent_step

    # Empty content → agent mode.
    assert _is_agent_step(SimpleNamespace(content="")) is True
    assert _is_agent_step(SimpleNamespace(content="   ")) is True
    # Marker present → agent mode.
    assert _is_agent_step(SimpleNamespace(content="please use [[agent]]")) is True
    assert _is_agent_step(SimpleNamespace(content="[[AGENT]]")) is True
    # Plain template body → template mode.
    assert _is_agent_step(SimpleNamespace(content="Hi {{first_name}}")) is False


@pytest.mark.asyncio
async def test_render_template_short_circuits_for_agent_mode():
    """Agent mode never goes through render_template — content is empty."""
    from app.workers.campaigns import render_template

    lead = SimpleNamespace(name="Pat", company="Co", email="p@x.test", domain="x.test")
    # Empty content, render_template returns "".
    assert render_template("", lead) == ""
