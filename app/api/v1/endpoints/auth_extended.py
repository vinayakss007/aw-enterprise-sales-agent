"""Extended auth endpoints: invite, accept-invite, forgot-password, reset-password.

These live in a separate module from the core auth.py to keep the PR diff
reviewable. They're wired into the same ``/auth/`` prefix in api.py.
"""
from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db
from app.core.config import settings
from app.core.security import get_password_hash
from app.db.models.user import User
from app.integrations.email.base import EmailMessage
from app.integrations.email.factory import get_email_sender
from app.services.admin.audit_service import AuditService
from app.services.auth.jwt import create_access_token

router = APIRouter()

# Token store — in production this would be Redis; for now we use a module-
# level dict which works for single-process deployments and tests.
_pending_invites: dict[str, dict] = {}  # token -> {email, tenant_id, role, expires}
_password_resets: dict[str, dict] = {}  # token -> {email, expires}


# --------------------------------------------------------------------------- #
# Schemas
# --------------------------------------------------------------------------- #


class InviteRequest(BaseModel):
    email: EmailStr
    role: str = "user"  # user | admin | viewer


class InviteResponse(BaseModel):
    token: str
    email: str
    expires_at: str


class AcceptInviteRequest(BaseModel):
    token: str
    name: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


# --------------------------------------------------------------------------- #
# Invitation flow
# --------------------------------------------------------------------------- #


@router.post("/invite", response_model=InviteResponse)
async def invite_user(
    payload: InviteRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Invite a user into the calling admin's tenant.

    Generates a one-time token valid for 72 hours. The invited person
    completes registration via ``POST /auth/accept-invite``.
    """
    # Don't allow inviting an email that already has an account.
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    if payload.role not in ("user", "admin", "viewer"):
        raise HTTPException(status_code=400, detail="Invalid role")

    token = secrets.token_urlsafe(32)
    expires = datetime.now(tz=UTC) + timedelta(hours=72)
    _pending_invites[token] = {
        "email": payload.email,
        "tenant_id": str(admin.tenant_id),
        "role": payload.role,
        "expires": expires.isoformat(),
        "invited_by": str(admin.id),
    }

    # Best-effort email delivery. If it fails the token is still usable
    # (admin can share the link manually).
    try:
        sender = get_email_sender()
        invite_url = f"{request.base_url}accept-invite?token={token}"
        await sender.send(EmailMessage(
            to=payload.email,
            subject=f"You're invited to join {admin.tenant.name if hasattr(admin, 'tenant') else 'the team'}",
            body=(
                f"You've been invited to join the Enterprise Sales Agent platform.\n\n"
                f"Click here to accept: {invite_url}\n\n"
                f"This link expires in 72 hours."
            ),
        ))
    except Exception:
        pass  # best-effort

    AuditService(db).record(
        tenant_id=str(admin.tenant_id),
        user_id=str(admin.id),
        action="user.invite",
        resource_type="user",
        resource_id=payload.email,
        changes_after={"email": payload.email, "role": payload.role},
        ip_address=request.client.host if request.client else None,
    )

    return InviteResponse(
        token=token,
        email=payload.email,
        expires_at=expires.isoformat(),
    )


@router.post("/accept-invite")
async def accept_invite(
    payload: AcceptInviteRequest,
    db: Session = Depends(get_db),
):
    """Accept an invitation and create the user under the inviter's tenant."""
    invite = _pending_invites.get(payload.token)
    if not invite:
        raise HTTPException(status_code=400, detail="Invalid or expired invitation token")

    expires = datetime.fromisoformat(invite["expires"])
    if datetime.now(tz=UTC) > expires:
        _pending_invites.pop(payload.token, None)
        raise HTTPException(status_code=400, detail="Invitation has expired")

    # Double-check email isn't taken (race condition guard).
    if db.query(User).filter(User.email == invite["email"]).first():
        _pending_invites.pop(payload.token, None)
        raise HTTPException(status_code=400, detail="User with this email already exists")

    user = User(
        id=uuid.uuid4(),
        tenant_id=invite["tenant_id"],
        email=invite["email"],
        name=payload.name,
        hashed_password=get_password_hash(payload.password),
        role=invite["role"],
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Consume the token.
    _pending_invites.pop(payload.token, None)

    # Auto-login: return a token so the UI can redirect to the dashboard.
    access_token = create_access_token(
        data={"sub": user.email, "user_id": str(user.id), "tenant_id": str(user.tenant_id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(user.id),
        "email": user.email,
        "role": user.role,
    }


# --------------------------------------------------------------------------- #
# Password reset
# --------------------------------------------------------------------------- #


@router.post("/forgot-password")
async def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Generate a password-reset token (1h TTL) and email it.

    Always returns 200 regardless of whether the email exists — prevents
    email enumeration.
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if user:
        token = secrets.token_urlsafe(32)
        _password_resets[token] = {
            "email": payload.email,
            "expires": (datetime.now(tz=UTC) + timedelta(hours=1)).isoformat(),
        }
        try:
            sender = get_email_sender()
            reset_url = f"{request.base_url}reset-password?token={token}"
            await sender.send(EmailMessage(
                to=payload.email,
                subject="Password reset request",
                body=(
                    f"Click here to reset your password: {reset_url}\n\n"
                    f"This link expires in 1 hour. If you didn't request this, ignore this email."
                ),
            ))
        except Exception:
            pass  # best-effort

    # Always 200 to prevent enumeration.
    return {"message": "If the email exists, a reset link has been sent."}


@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """Validate the reset token, update the user's password."""
    record = _password_resets.get(payload.token)
    if not record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    expires = datetime.fromisoformat(record["expires"])
    if datetime.now(tz=UTC) > expires:
        _password_resets.pop(payload.token, None)
        raise HTTPException(status_code=400, detail="Reset token has expired")

    user = db.query(User).filter(User.email == record["email"]).first()
    if not user:
        _password_resets.pop(payload.token, None)
        raise HTTPException(status_code=400, detail="User not found")

    user.hashed_password = get_password_hash(payload.new_password)
    user.updated_at = datetime.utcnow()
    db.commit()

    # Consume the token.
    _password_resets.pop(payload.token, None)

    return {"message": "Password updated successfully"}


# Expose the stores for testing.
__all__ = ["router", "_pending_invites", "_password_resets"]
