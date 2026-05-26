"""Admin user management endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.user import User
from app.api.deps import get_current_admin
from app.services.admin.user_service import UserService

router = APIRouter()


@router.get("/")
async def list_users(
    tenant_id: str = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    service = UserService(db)
    users = service.get_users(tenant_id=tenant_id, skip=skip, limit=limit)
    return {"users": [
        {
            "id": str(u.id),
            "email": u.email,
            "name": u.name,
            "role": u.role,
            "is_active": u.is_active,
            "tenant_id": str(u.tenant_id),
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]}


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    service = UserService(db)
    if not service.deactivate_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deactivated"}


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    service = UserService(db)
    if not service.activate_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User activated"}
