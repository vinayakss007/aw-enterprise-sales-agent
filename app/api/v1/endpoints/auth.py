"""Auth endpoints + audit hooks.

Successful and failed logins are written to the audit chain so security
incidents (credential stuffing, account takeover) leave a permanent trail.
``register`` writes a ``user.create`` action against the new tenant.
"""
from __future__ import annotations

import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.user import Token, UserCreate, UserResponse
from app.services.admin.audit_service import AuditService
from app.services.auth.jwt import authenticate_user, create_access_token, get_current_user

router = APIRouter()


def _audit_context(request: Request) -> dict:
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


@router.post("/token", response_model=Token)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    audit = AuditService(db)
    if not user:
        # Look up the user we *tried* to authenticate as so the audit row is
        # tenant-scoped when possible. Failed attempts against unknown
        # accounts stay anonymous.
        attempted = (
            db.query(User).filter(User.email == form_data.username).first()
        )
        if attempted is not None:
            audit.record(
                tenant_id=str(attempted.tenant_id),
                user_id=str(attempted.id),
                action="login.failed",
                resource_type="user",
                resource_id=str(attempted.id),
                changes_after={"reason": "bad_password"},
                **_audit_context(request),
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={
            "sub": user.email,
            "user_id": str(user.id),
            "tenant_id": str(user.tenant_id),
        },
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    audit.record(
        tenant_id=str(user.tenant_id),
        user_id=str(user.id),
        action="login.success",
        resource_type="user",
        resource_id=str(user.id),
        **_audit_context(request),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_in: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(
            status_code=400, detail="User with this email already exists"
        )

    # Use the same UUID for the new tenant + flush a Tenant row so the
    # audit FK constraint is satisfied. Without this, register would
    # produce orphan users (user.tenant_id pointing at no tenant) and
    # audit rows would fail to insert with a FK violation.
    from app.db.models.tenant import Tenant

    tenant_id = uuid.uuid4()
    tenant = Tenant(id=tenant_id, name=user_in.name + "'s workspace")
    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        email=user_in.email,
        name=user_in.name,
        hashed_password=get_password_hash(user_in.password),
        role="owner",
    )
    db.add(tenant)
    db.add(user)
    db.commit()
    db.refresh(user)

    AuditService(db).record(
        tenant_id=str(tenant_id),
        user_id=str(user.id),
        action="user.create",
        resource_type="user",
        resource_id=str(user.id),
        changes_after={"email": user.email, "role": user.role},
        **_audit_context(request),
    )
    return user


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
