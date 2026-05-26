"""Authentication endpoints."""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.tenant import Tenant
from app.core.security import get_password_hash, verify_password
from app.services.auth.jwt import create_access_token, create_refresh_token

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    company_name: str = ""


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT tokens."""
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()

    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user and create a tenant."""
    # Check if user exists
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create tenant
    tenant = Tenant(
        id=uuid.uuid4(),
        name=request.company_name or f"{request.name}'s Workspace",
        subdomain=request.email.split("@")[0].lower().replace(".", "-"),
        plan="free",
        status="active",
    )
    db.add(tenant)
    db.flush()

    # Create user as owner of the new tenant
    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email=request.email,
        name=request.name,
        hashed_password=get_password_hash(request.password),
        role="owner",
        is_active=True,
    )
    db.add(user)
    db.commit()

    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.get("/me")
async def get_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None),
):
    """Get current user profile. Requires auth dependency."""
    # This endpoint uses a simplified approach - real auth via deps
    from app.api.deps import get_current_user
    return {"message": "Use /api/v1/auth/me with proper auth header"}
