import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.user import Token, UserCreate, UserResponse
from app.services.auth.jwt import authenticate_user, create_access_token, get_current_user

router = APIRouter()

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": str(user.id), "tenant_id": str(user.tenant_id)},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=UserResponse)
async def register_user(
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists"
        )

    # Create new tenant + user. The Tenant row is required because
    # ``User.tenant_id`` is a ForeignKey with ON DELETE CASCADE; without it
    # the insert would fail with a FK violation in Postgres.
    from app.db.models.tenant import Tenant

    hashed_password = get_password_hash(user_in.password)
    tenant_id = uuid.uuid4()
    tenant = Tenant(id=tenant_id, name=f"{user_in.name}'s workspace")
    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        email=user_in.email,
        name=user_in.name,
        hashed_password=hashed_password,
        role="owner"
    )

    db.add(tenant)
    db.add(user)
    db.commit()
    db.refresh(user)

    return user

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user