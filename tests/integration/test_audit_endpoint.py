"""End-to-end audit endpoint tests."""
from __future__ import annotations


def _register_admin(client, email: str = "admin-audit@acme.test") -> str:
    """Register an owner user and return their bearer token."""
    register = client.post(
        "/api/v1/auth/register",
        json={"email": email, "name": "Admin", "password": "hunter22"},
    )
    assert register.status_code == 200, register.text
    token = client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": "hunter22"},
    )
    assert token.status_code == 200
    return token.json()["access_token"]


def test_list_audit_logs_returns_register_and_login_rows(client):
    token = _register_admin(client, "audit1@acme.test")
    # Fire a couple of extra audited actions.
    client.post(
        "/api/v1/auth/token",
        data={"username": "audit1@acme.test", "password": "hunter22"},
    )
    client.post(
        "/api/v1/auth/token",
        data={"username": "audit1@acme.test", "password": "WRONG"},
    )

    resp = client.get(
        "/api/v1/admin/audit/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    rows = resp.json()
    actions = {r["action"] for r in rows}
    assert "user.create" in actions
    assert "login.success" in actions
    assert "login.failed" in actions

    # All rows must have a hash and be ordered timestamp-desc.
    assert all(len(r["current_hash"]) == 64 for r in rows)
    timestamps = [r["timestamp"] for r in rows]
    assert timestamps == sorted(timestamps, reverse=True)


def test_audit_logs_filterable_by_action(client):
    token = _register_admin(client, "audit2@acme.test")
    resp = client.get(
        "/api/v1/admin/audit/",
        params={"action": "login.success"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    actions = {r["action"] for r in resp.json()}
    assert actions == {"login.success"}


def test_audit_logs_are_tenant_scoped(client):
    """Two different tenants must see disjoint audit rows."""
    token_a = _register_admin(client, "tenant-a@example.test")
    token_b = _register_admin(client, "tenant-b@example.test")

    rows_a = client.get(
        "/api/v1/admin/audit/",
        headers={"Authorization": f"Bearer {token_a}"},
    ).json()
    rows_b = client.get(
        "/api/v1/admin/audit/",
        headers={"Authorization": f"Bearer {token_b}"},
    ).json()

    # No tenant_id from A appears in B's rows or vice versa.
    a_tenant_ids = {r["tenant_id"] for r in rows_a}
    b_tenant_ids = {r["tenant_id"] for r in rows_b}
    assert a_tenant_ids and b_tenant_ids
    assert a_tenant_ids.isdisjoint(b_tenant_ids)


def test_verify_chain_returns_intact_for_fresh_tenant(client):
    token = _register_admin(client, "verify@acme.test")
    resp = client.get(
        "/api/v1/admin/audit/verify",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["verified"] is True
    assert body["count"] >= 1  # at least the user.create row
    assert body["broken_at"] == []


def test_verify_chain_detects_tampering(client, db_session):
    """Mutate a row directly in the DB and confirm the endpoint flags it."""
    from app.db.models.audit_log import AuditLog
    from app.db.models.user import User

    token = _register_admin(client, "tamper@acme.test")
    user = db_session.query(User).filter(User.email == "tamper@acme.test").one()
    # Tamper with the most recent audit row for this tenant.
    row = (
        db_session.query(AuditLog)
        .filter(AuditLog.tenant_id == user.tenant_id)
        .order_by(AuditLog.id.desc())
        .first()
    )
    assert row is not None
    row.action = "TAMPERED"
    db_session.commit()

    resp = client.get(
        "/api/v1/admin/audit/verify",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["verified"] is False
    assert row.id in body["broken_at"]


def test_audit_endpoints_require_auth(client):
    list_resp = client.get("/api/v1/admin/audit/")
    verify_resp = client.get("/api/v1/admin/audit/verify")
    assert list_resp.status_code in (401, 403)
    assert verify_resp.status_code in (401, 403)
