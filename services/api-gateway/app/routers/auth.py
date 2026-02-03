from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.user_service import find_or_create_user
from app.dependencies import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Simple email-based login for Phase-1.
    In production, this would send a magic link and verify it.
    For development, it directly issues a JWT.
    """
    user = await find_or_create_user(db, email=request.email)
    token = create_access_token(email=user.email)
    return TokenResponse(access_token=token)
