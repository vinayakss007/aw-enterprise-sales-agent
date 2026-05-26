"""FastAPI dependency injectors.

Roles hierarchy (highest to lowest):
  superadmin  — platform operator, bypasses tenant scoping entirely
  owner       — tenant creator, full control within their tenant
  admin       — tenant-level admin
  user        — standard member
  viewer      — read-only

Guards:
  get_current_user        — any authenticated, active user
  get_current_admin       — owner | admin | superadmin
  get_current_superadmin  — superadmin only (cross-tenant operations)
"""
from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.db.session import SessionLocal
from app.services.auth.jwt import verify_token

security = HTTPBearer()

SUPERADMIN_ROLE = "superadmin"
ADMIN_ROLES = {"superadmin", "owner", "admin"}


def get_db() -> Generator[Session, None, None]:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    email = verify_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Owner, admin, or superadmin."""
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Admin privileges required",
        )
    return current_user


async def get_current_superadmin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Platform-level superadmin only. For cross-tenant operations."""
    if current_user.role != SUPERADMIN_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Superadmin privileges required",
        )
    return current_user