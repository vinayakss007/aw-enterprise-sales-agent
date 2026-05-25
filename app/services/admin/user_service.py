from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models.user import User
from app.schemas.user import UserResponse, UserUpdate


class UserService:
    def __init__(self, db: Session):
        self.db = db

    async def get_all_users(self, skip: int = 0, limit: int = 50) -> list[UserResponse]:
        """
        Get all users across all tenants
        """
        users = self.db.query(User).offset(skip).limit(limit).all()
        
        return [
            UserResponse(
                id=str(user.id),
                email=user.email,
                name=user.name,
                role=user.role,
                tenant_id=str(user.tenant_id),
                is_active=user.is_active,
                is_verified=user.is_verified,
                last_login_at=user.last_login_at,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            for user in users
        ]

    async def get_user(self, user_id: str) -> UserResponse | None:
        """
        Get a specific user by ID
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return None
            
        return UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            role=user.role,
            tenant_id=str(user.tenant_id),
            is_active=user.is_active,
            is_verified=user.is_verified,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    async def update_user(self, user_id: str, user_in: UserUpdate) -> UserResponse | None:
        """
        Update user information
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return None

        # Update allowed fields
        update_data = user_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)

        return UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            role=user.role,
            tenant_id=str(user.tenant_id),
            is_active=user.is_active,
            is_verified=user.is_verified,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    async def update_user_role(self, user_id: str, role: str) -> bool:
        """
        Update user role
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return False

        user.role = role
        user.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    async def delete_user(self, user_id: str) -> bool:
        """
        Delete user (soft delete by deactivation)
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return False

        user.is_active = False
        user.updated_at = datetime.utcnow()
        self.db.commit()
        return True