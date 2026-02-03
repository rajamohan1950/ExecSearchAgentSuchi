from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.services.user_service import update_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    updates: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    updated = await update_user(
        db,
        user,
        name=updates.name,
        phone=updates.phone,
        location=updates.location,
        linkedin_url=updates.linkedin_url,
    )
    return updated
