"""Dependency guard tests for the new role hierarchy."""
from __future__ import annotations

from types import SimpleNamespace

import pytest


def _user(role: str, is_active: bool = True):
    return SimpleNamespace(
        id="u1", email="a@b.test", role=role, is_active=is_active, tenant_id="t1"
    )


@pytest.mark.asyncio
async def test_get_current_admin_allows_superadmin():
    from app.api.deps import get_current_admin

    user = _user("superadmin")
    result = await get_current_admin(user)
    assert result.role == "superadmin"


@pytest.mark.asyncio
async def test_get_current_admin_allows_owner():
    from app.api.deps import get_current_admin

    result = await get_current_admin(_user("owner"))
    assert result.role == "owner"


@pytest.mark.asyncio
async def test_get_current_admin_rejects_user():
    from fastapi import HTTPException

    from app.api.deps import get_current_admin

    with pytest.raises(HTTPException) as exc:
        await get_current_admin(_user("user"))
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_get_current_admin_rejects_viewer():
    from fastapi import HTTPException

    from app.api.deps import get_current_admin

    with pytest.raises(HTTPException) as exc:
        await get_current_admin(_user("viewer"))
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_get_current_superadmin_rejects_owner():
    from fastapi import HTTPException

    from app.api.deps import get_current_superadmin

    with pytest.raises(HTTPException) as exc:
        await get_current_superadmin(_user("owner"))
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_get_current_superadmin_allows_superadmin():
    from app.api.deps import get_current_superadmin

    result = await get_current_superadmin(_user("superadmin"))
    assert result.role == "superadmin"
