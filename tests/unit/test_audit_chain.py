"""Audit chain hash function unit tests."""
from __future__ import annotations


def test_compute_hash_is_deterministic():
    from app.services.admin.audit_service import compute_hash

    record = {"action": "login.success", "user_id": "u1", "tenant_id": "t1"}
    a = compute_hash("prev", record)
    b = compute_hash("prev", record)
    assert a == b
    assert len(a) == 64  # sha256 hex


def test_compute_hash_changes_with_previous_hash():
    from app.services.admin.audit_service import compute_hash

    record = {"action": "login.success"}
    h1 = compute_hash("", record)
    h2 = compute_hash(h1, record)
    assert h1 != h2


def test_compute_hash_changes_with_payload():
    from app.services.admin.audit_service import compute_hash

    h1 = compute_hash("p", {"action": "login.success"})
    h2 = compute_hash("p", {"action": "login.failed"})
    assert h1 != h2


def test_compute_hash_canonicalises_key_order():
    """{a:1, b:2} and {b:2, a:1} must hash to the same value."""
    from app.services.admin.audit_service import compute_hash

    h1 = compute_hash("", {"a": 1, "b": 2})
    h2 = compute_hash("", {"b": 2, "a": 1})
    assert h1 == h2
