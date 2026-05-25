"""End-to-end audit chain tests against a real Postgres."""
from __future__ import annotations

import uuid

import pytest


@pytest.fixture()
def tenant(db_session):
    from app.db.models.tenant import Tenant

    t = Tenant(id=uuid.uuid4(), name="AuditCo")
    db_session.add(t)
    db_session.commit()
    return t


def test_record_writes_chain_with_first_previous_hash_empty(db_session, tenant):
    from app.db.models.audit_log import AuditLog
    from app.services.admin.audit_service import AuditService

    audit = AuditService(db_session)
    e1 = audit.record(
        tenant_id=str(tenant.id),
        action="login.success",
        resource_type="user",
        resource_id="u1",
    )
    assert e1 is not None
    assert e1.previous_hash == ""
    assert len(e1.current_hash) == 64

    e2 = audit.record(
        tenant_id=str(tenant.id),
        action="lead.create",
        resource_type="lead",
        resource_id="l1",
    )
    assert e2 is not None
    assert e2.previous_hash == e1.current_hash
    assert e2.current_hash != e1.current_hash

    rows = (
        db_session.query(AuditLog)
        .filter(AuditLog.tenant_id == tenant.id)
        .order_by(AuditLog.id.asc())
        .all()
    )
    assert [r.id for r in rows] == [e1.id, e2.id]


def test_chains_are_independent_per_tenant(db_session):
    from app.db.models.tenant import Tenant
    from app.services.admin.audit_service import AuditService

    a = Tenant(id=uuid.uuid4(), name="A")
    b = Tenant(id=uuid.uuid4(), name="B")
    db_session.add_all([a, b])
    db_session.commit()

    audit = AuditService(db_session)
    a1 = audit.record(tenant_id=str(a.id), action="x", resource_type="r", resource_id="1")
    b1 = audit.record(tenant_id=str(b.id), action="x", resource_type="r", resource_id="1")
    a2 = audit.record(tenant_id=str(a.id), action="y", resource_type="r", resource_id="2")

    assert a1.previous_hash == ""
    assert b1.previous_hash == ""
    assert a2.previous_hash == a1.current_hash


def test_verify_chain_detects_intact_chain(db_session, tenant):
    from app.services.admin.audit_service import AuditService

    audit = AuditService(db_session)
    for i in range(5):
        audit.record(
            tenant_id=str(tenant.id),
            action=f"action.{i}",
            resource_type="resource",
            resource_id=str(i),
        )

    result = audit.verify_chain(str(tenant.id))
    assert result == {"verified": True, "count": 5, "broken_at": []}


def test_verify_chain_detects_tampering(db_session, tenant):
    """Mutating the changes_after of any row breaks the chain."""
    from app.db.models.audit_log import AuditLog
    from app.services.admin.audit_service import AuditService

    audit = AuditService(db_session)
    for i in range(3):
        audit.record(
            tenant_id=str(tenant.id),
            action=f"a{i}",
            resource_type="r",
            resource_id=str(i),
        )

    # Tamper with the middle row — change the action without recomputing
    # the hash. This is the realistic "DB attacker" scenario.
    rows = (
        db_session.query(AuditLog)
        .filter(AuditLog.tenant_id == tenant.id)
        .order_by(AuditLog.id.asc())
        .all()
    )
    rows[1].action = "TAMPERED"
    db_session.commit()

    result = audit.verify_chain(str(tenant.id))
    assert result["verified"] is False
    assert rows[1].id in result["broken_at"]


def test_verify_chain_detects_deletion(db_session, tenant):
    """Deleting a middle row breaks the chain at the surviving successor."""
    from app.db.models.audit_log import AuditLog
    from app.services.admin.audit_service import AuditService

    audit = AuditService(db_session)
    e1 = audit.record(tenant_id=str(tenant.id), action="a", resource_type="r", resource_id="1")
    e2 = audit.record(tenant_id=str(tenant.id), action="b", resource_type="r", resource_id="2")
    e3 = audit.record(tenant_id=str(tenant.id), action="c", resource_type="r", resource_id="3")

    db_session.query(AuditLog).filter(AuditLog.id == e2.id).delete()
    db_session.commit()

    result = audit.verify_chain(str(tenant.id))
    # e3.previous_hash still references e2, so the chain breaks at e3.
    assert result["verified"] is False
    assert e3.id in result["broken_at"]
    # First row is untouched and still verifies.
    assert e1.id not in result["broken_at"]


def test_login_writes_audit_entries(client, db_session):
    """Successful + failed logins write to the chain."""
    from app.db.models.audit_log import AuditLog
    from app.db.models.user import User
    from app.services.admin.audit_service import AuditService

    register = client.post(
        "/api/v1/auth/register",
        json={"email": "audit@acme.test", "name": "Audit", "password": "hunter22"},
    )
    assert register.status_code == 200, register.text

    ok = client.post(
        "/api/v1/auth/token",
        data={"username": "audit@acme.test", "password": "hunter22"},
    )
    assert ok.status_code == 200

    bad = client.post(
        "/api/v1/auth/token",
        data={"username": "audit@acme.test", "password": "WRONG"},
    )
    assert bad.status_code == 401

    user = db_session.query(User).filter(User.email == "audit@acme.test").one()
    rows = (
        db_session.query(AuditLog)
        .filter(AuditLog.tenant_id == user.tenant_id)
        .order_by(AuditLog.id.asc())
        .all()
    )
    actions = [r.action for r in rows]
    assert "user.create" in actions
    assert "login.success" in actions
    assert "login.failed" in actions
    assert (
        AuditService(db_session).verify_chain(str(user.tenant_id))["verified"]
        is True
    )
