"""End-to-end auth flow against a real Postgres."""
from __future__ import annotations


def test_register_then_login(client):
    register = client.post(
        "/api/v1/auth/register",
        json={"email": "alice@example.com", "name": "Alice", "password": "hunter22"},
    )
    assert register.status_code == 200, register.text
    body = register.json()
    assert body["email"] == "alice@example.com"
    assert body["role"] == "owner"

    # Duplicate registration is rejected.
    dup = client.post(
        "/api/v1/auth/register",
        json={"email": "alice@example.com", "name": "Alice 2", "password": "hunter22"},
    )
    assert dup.status_code == 400

    # Token endpoint takes form data (OAuth2PasswordRequestForm).
    token_resp = client.post(
        "/api/v1/auth/token",
        data={"username": "alice@example.com", "password": "hunter22"},
    )
    assert token_resp.status_code == 200, token_resp.text
    token = token_resp.json()["access_token"]
    assert token

    # /me returns the current user.
    me = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert me.status_code == 200, me.text
    assert me.json()["email"] == "alice@example.com"


def test_login_with_wrong_password_rejected(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "bob@example.com", "name": "Bob", "password": "rightpass1"},
    )
    bad = client.post(
        "/api/v1/auth/token",
        data={"username": "bob@example.com", "password": "wrongpass"},
    )
    assert bad.status_code == 401


def test_me_requires_auth(client):
    resp = client.get("/api/v1/auth/me")
    # FastAPI's HTTPBearer returns 403 when no Authorization header is sent.
    assert resp.status_code in (401, 403)
