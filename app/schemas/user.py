from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr


class RoleEnum(str, Enum):
    owner = "owner"
    admin = "admin"
    user = "user"
    viewer = "viewer"

class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: str | None = None
    role: RoleEnum | None = None

class UserResponse(UserBase):
    id: str
    tenant_id: str
    role: RoleEnum
    is_active: bool
    is_verified: bool
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None
    user_id: str | None = None
    tenant_id: str | None = None