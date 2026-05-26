"""User administration service."""
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.models.user import User


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_users(self, tenant_id: str = None, skip: int = 0, limit: int = 50) -> List[User]:
        query = self.db.query(User)
        if tenant_id:
            query = query.filter(User.tenant_id == tenant_id)
        return query.offset(skip).limit(limit).all()

    def get_user(self, user_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def deactivate_user(self, user_id: str) -> bool:
        user = self.get_user(user_id)
        if not user:
            return False
        user.is_active = False
        user.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    def activate_user(self, user_id: str) -> bool:
        user = self.get_user(user_id)
        if not user:
            return False
        user.is_active = True
        user.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    def update_role(self, user_id: str, role: str) -> bool:
        user = self.get_user(user_id)
        if not user:
            return False
        if role not in ("owner", "admin", "user", "viewer"):
            return False
        user.role = role
        user.updated_at = datetime.utcnow()
        self.db.commit()
        return True
