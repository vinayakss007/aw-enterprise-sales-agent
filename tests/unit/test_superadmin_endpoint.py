"""Unit tests for superadmin endpoint logic.

These tests exercise the endpoint guards and validation without requiring
a real database (no TEST_DATABASE_URL needed).
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException


def _user(role: str = "user", is_active: bool = True):
    return SimpleNamespace(
        id="u1",
        email="test@example.com",
        name="Test User",
        role=role,
        is_active=is_active,
        tenant_id="t1",
    )


@pytest.mark.asyncio
async def test_overview_endpoint_requires_superadmin():
    """A normal user (role=user) should get 403 from the superadmin guard."""
    from app.api.deps import get_current_superadmin

    normal_user = _user(role="user")
    with pytest.raises(HTTPException) as exc_info:
        await get_current_superadmin(normal_user)
    assert exc_info.value.status_code == 403

    # Also verify that owner role is rejected.
    owner_user = _user(role="owner")
    with pytest.raises(HTTPException) as exc_info:
        await get_current_superadmin(owner_user)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_set_user_role_validates_role_value():
    """The set_user_role endpoint rejects invalid role values with 400."""
    from app.api.v1.endpoints.superadmin import set_user_role, SetUserRoleRequest

    # Mock the DB session.
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = _user(role="user")

    superadmin_user = _user(role="superadmin")
    payload = SetUserRoleRequest(role="invalid_role")

    with pytest.raises(HTTPException) as exc_info:
        await set_user_role(
            user_id="u1",
            payload=payload,
            db=mock_db,
            _sa=superadmin_user,
        )
    assert exc_info.value.status_code == 400
    assert "Invalid role" in exc_info.value.detail
