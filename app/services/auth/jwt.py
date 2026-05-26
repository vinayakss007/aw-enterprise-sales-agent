"""JWT helpers and password hashing.

Uses ``python-jose`` (declared in requirements.txt). Token payload uses ``sub``
for the user's email; ``user_id`` and ``tenant_id`` are also embedded so other
layers can avoid an extra DB lookup when they only need the IDs.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(tz=UTC) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str) -> str | None:
    """Decode a token and return the ``sub`` (email) claim, or None."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
    email = payload.get("sub")
    return email if isinstance(email, str) else None


async def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


# Backwards-compat shim so existing imports keep resolving. The real
# request-bound dependency lives in ``app.api.deps.get_current_user``.
def get_current_user(token: str) -> User | None:  # pragma: no cover
    raise NotImplementedError(
        "Use app.api.deps.get_current_user — this stub only exists for legacy imports."
    )


__all__ = [
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "verify_token",
    "authenticate_user",
    "get_current_user",
]
