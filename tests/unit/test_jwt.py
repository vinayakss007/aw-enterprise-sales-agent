"""JWT helpers — no DB required."""
from __future__ import annotations

from datetime import timedelta


def test_password_hash_round_trip():
    from app.services.auth.jwt import get_password_hash, verify_password

    hashed = get_password_hash("hunter2")
    assert hashed != "hunter2"
    assert verify_password("hunter2", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_create_and_verify_token_round_trip():
    from app.services.auth.jwt import create_access_token, verify_token

    token = create_access_token({"sub": "alice@example.com", "user_id": "u1"})
    assert isinstance(token, str)
    assert verify_token(token) == "alice@example.com"


def test_verify_token_returns_none_for_garbage():
    from app.services.auth.jwt import verify_token

    assert verify_token("not-a-token") is None
    assert verify_token("") is None


def test_token_expires():
    from app.services.auth.jwt import create_access_token, verify_token

    expired = create_access_token(
        {"sub": "alice@example.com"}, expires_delta=timedelta(seconds=-1)
    )
    assert verify_token(expired) is None
