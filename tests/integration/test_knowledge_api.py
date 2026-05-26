"""End-to-end knowledge-base endpoint tests."""
from __future__ import annotations


def _register_and_login(client, email: str = "kb@target.test") -> str:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "name": "KB", "password": "hunter22"},
    )
    resp = client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": "hunter22"},
    )
    return resp.json()["access_token"]


def test_create_list_get_update_archive_roundtrip(client):
    token = _register_and_login(client, "kb1@target.test")
    headers = {"Authorization": f"Bearer {token}"}

    create = client.post(
        "/api/v1/customer/knowledge/",
        json={
            "title": "Enterprise pricing",
            "content": "Plans start at $99/mo and scale per seat.",
            "category": "pricing",
            "tags": ["pricing", "enterprise"],
        },
        headers=headers,
    )
    assert create.status_code == 200, create.text
    entry_id = create.json()["id"]
    assert create.json()["active"] is True

    listing = client.get("/api/v1/customer/knowledge/", headers=headers)
    assert listing.status_code == 200
    assert any(e["id"] == entry_id for e in listing.json())

    fetched = client.get(
        f"/api/v1/customer/knowledge/{entry_id}", headers=headers
    )
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "Enterprise pricing"

    updated = client.put(
        f"/api/v1/customer/knowledge/{entry_id}",
        json={"title": "Pricing 2026"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Pricing 2026"

    archived = client.delete(
        f"/api/v1/customer/knowledge/{entry_id}", headers=headers
    )
    assert archived.status_code == 200

    refetch = client.get(
        f"/api/v1/customer/knowledge/{entry_id}", headers=headers
    )
    assert refetch.status_code == 200
    assert refetch.json()["active"] is False


def test_list_active_only_filters_archived(client):
    token = _register_and_login(client, "kb2@target.test")
    headers = {"Authorization": f"Bearer {token}"}

    a = client.post(
        "/api/v1/customer/knowledge/",
        json={"title": "A", "content": "alpha"},
        headers=headers,
    ).json()
    b = client.post(
        "/api/v1/customer/knowledge/",
        json={"title": "B", "content": "beta"},
        headers=headers,
    ).json()
    # Archive B.
    client.delete(f"/api/v1/customer/knowledge/{b['id']}", headers=headers)

    active_only = client.get(
        "/api/v1/customer/knowledge/", headers=headers
    ).json()
    assert any(e["id"] == a["id"] for e in active_only)
    assert all(e["id"] != b["id"] for e in active_only)

    all_entries = client.get(
        "/api/v1/customer/knowledge/?active_only=false", headers=headers
    ).json()
    assert any(e["id"] == b["id"] for e in all_entries)


def test_lookup_finds_by_keyword_and_ranks_title_higher_than_content(client):
    token = _register_and_login(client, "kb3@target.test")
    headers = {"Authorization": f"Bearer {token}"}

    title_match = client.post(
        "/api/v1/customer/knowledge/",
        json={"title": "Pricing FAQ", "content": "Generic content"},
        headers=headers,
    ).json()
    content_match = client.post(
        "/api/v1/customer/knowledge/",
        json={"title": "Onboarding", "content": "Has a pricing line in it"},
        headers=headers,
    ).json()

    resp = client.get(
        "/api/v1/customer/knowledge/lookup?q=pricing&limit=5",
        headers=headers,
    )
    assert resp.status_code == 200
    matches = resp.json()
    assert len(matches) >= 2
    # Title hit should rank first.
    assert matches[0]["id"] == title_match["id"]
    assert any(m["id"] == content_match["id"] for m in matches)


def test_lookup_drops_stopwords(client):
    """A query that is 100% stopwords returns []."""
    token = _register_and_login(client, "kb4@target.test")
    headers = {"Authorization": f"Bearer {token}"}
    client.post(
        "/api/v1/customer/knowledge/",
        json={"title": "Anything", "content": "anything"},
        headers=headers,
    )
    resp = client.get(
        "/api/v1/customer/knowledge/lookup?q=the%20a%20of",
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json() == []


def test_knowledge_endpoints_tenant_scoped(client):
    """Tenant A's entries must not appear in tenant B's lookups."""
    token_a = _register_and_login(client, "tenant-a-kb@target.test")
    token_b = _register_and_login(client, "tenant-b-kb@target.test")

    a_entry = client.post(
        "/api/v1/customer/knowledge/",
        json={"title": "Secret pricing", "content": "$$$"},
        headers={"Authorization": f"Bearer {token_a}"},
    ).json()

    b_listing = client.get(
        "/api/v1/customer/knowledge/",
        headers={"Authorization": f"Bearer {token_b}"},
    ).json()
    assert all(e["id"] != a_entry["id"] for e in b_listing)

    b_fetch = client.get(
        f"/api/v1/customer/knowledge/{a_entry['id']}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert b_fetch.status_code == 404

    b_lookup = client.get(
        "/api/v1/customer/knowledge/lookup?q=secret",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert b_lookup.status_code == 200
    assert b_lookup.json() == []


def test_knowledge_endpoints_require_auth(client):
    assert client.get("/api/v1/customer/knowledge/").status_code in (401, 403)
    assert client.post(
        "/api/v1/customer/knowledge/",
        json={"title": "x", "content": "y"},
    ).status_code in (401, 403)


def test_create_and_update_write_audit_rows(client, db_session):
    from app.db.models.audit_log import AuditLog
    from app.db.models.user import User

    token = _register_and_login(client, "kb-audit@target.test")
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post(
        "/api/v1/customer/knowledge/",
        json={"title": "T", "content": "C"},
        headers=headers,
    ).json()
    client.put(
        f"/api/v1/customer/knowledge/{created['id']}",
        json={"title": "T2"},
        headers=headers,
    )
    client.delete(f"/api/v1/customer/knowledge/{created['id']}", headers=headers)

    user = db_session.query(User).filter(User.email == "kb-audit@target.test").one()
    actions = [
        r.action
        for r in db_session.query(AuditLog)
        .filter(AuditLog.tenant_id == user.tenant_id)
        .all()
    ]
    assert "knowledge.create" in actions
    assert "knowledge.update" in actions
    assert "knowledge.delete" in actions
