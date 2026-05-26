"""Tests for authentication."""
import pytest
from app.services.auth.jwt import create_access_token, create_refresh_token, verify_token
from app.core.security import get_password_hash, verify_password


class TestJWT:
    def test_create_and_verify_token(self):
        token = create_access_token(data={"sub": "test@example.com"})
        email = verify_token(token)
        assert email == "test@example.com"

    def test_invalid_token_returns_none(self):
        result = verify_token("invalid.token.here")
        assert result is None

    def test_refresh_token_creates_valid_token(self):
        token = create_refresh_token(data={"sub": "user@test.com"})
        email = verify_token(token)
        assert email == "user@test.com"


class TestPasswordHashing:
    def test_hash_and_verify(self):
        password = "my-secure-password-123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed) is True

    def test_wrong_password_fails(self):
        hashed = get_password_hash("correct")
        assert verify_password("wrong", hashed) is False

    def test_different_hashes_for_same_password(self):
        password = "test123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        # bcrypt uses random salt, so hashes differ
        assert hash1 != hash2
        # But both verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True
