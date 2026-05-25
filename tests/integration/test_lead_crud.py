"""Lead CRUD behaviour with tenant isolation."""
from __future__ import annotations


def _register_and_login(client, email: str) -> str:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "name": email.split("@")[0], "password": "hunter22"},
    )
    resp = client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": "hunter22"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def test_lead_create_and_list(client):
    token = _register_and_login(client, "owner1@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create = client.post(
        "/api/v1/customer/leads/",
        json={
            "email": "lead@target.test",
            "name": "Lead Person",
            "company": "Target",
        },
        headers=headers,
    )
    assert create.status_code == 200, create.text
    lead_id = create.json()["id"]
    assert create.json()["company"] == "Target"

    listing = client.get("/api/v1/customer/leads/", headers=headers)
    assert listing.status_code == 200
    ids = {lead["id"] for lead in listing.json()}
    assert lead_id in ids


def test_lead_update_and_archive(client):
    token = _register_and_login(client, "owner2@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create = client.post(
        "/api/v1/customer/leads/",
        json={"email": "x@target.test", "name": "X", "company": "Target"},
        headers=headers,
    )
    lead_id = create.json()["id"]

    upd = client.put(
        f"/api/v1/customer/leads/{lead_id}",
        json={"status": "qualified"},
        headers=headers,
    )
    assert upd.status_code == 200
    assert upd.json()["status"] == "qualified"

    archive = client.delete(
        f"/api/v1/customer/leads/{lead_id}", headers=headers
    )
    assert archive.status_code == 200

    refetch = client.get(
        f"/api/v1/customer/leads/{lead_id}", headers=headers
    )
    assert refetch.status_code == 200
    assert refetch.json()["status"] == "archived"


def test_tenant_isolation(client):
    """A user must not see another tenant's leads."""
    token_a = _register_and_login(client, "tenant_a@example.com")
    token_b = _register_and_login(client, "tenant_b@example.com")

    create = client.post(
        "/api/v1/customer/leads/",
        json={"email": "private@target.test", "name": "Private"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert create.status_code == 200
    lead_id = create.json()["id"]

    # Tenant B sees an empty list.
    listing_b = client.get(
        "/api/v1/customer/leads/",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert listing_b.status_code == 200
    assert all(lead["id"] != lead_id for lead in listing_b.json())

    # And cannot fetch the lead by id.
    fetch_b = client.get(
        f"/api/v1/customer/leads/{lead_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert fetch_b.status_code == 404
