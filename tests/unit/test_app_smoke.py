"""Smoke tests verifying the FastAPI app boots and key routes are wired."""
from __future__ import annotations


def test_app_imports():
    from app.main import app

    assert app.title == "Enterprise Sales Agent"


def test_health_endpoint_responds():
    """``/api/v1/health`` should return 200 even with no DB available."""
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        resp = client.get("/api/v1/health")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert body["service"] == "sales-agent-platform"


def test_known_routes_registered():
    from app.main import app

    paths = {route.path for route in app.routes}
    # A representative slice of the contract — if any of these disappear, a
    # frontend page is going to break.
    expected_subset = {
        "/api/v1/auth/token",
        "/api/v1/auth/register",
        "/api/v1/auth/me",
        "/api/v1/customer/leads/",
        "/api/v1/customer/agent/execute/{lead_id}",
        "/api/v1/customer/campaigns/",
        "/api/v1/customer/crm/sync/{lead_id}",
        "/api/v1/admin/users/",
        "/api/v1/admin/tenants/",
        "/api/v1/health",
    }
    missing = expected_subset - paths
    assert not missing, f"Missing routes: {missing}"
