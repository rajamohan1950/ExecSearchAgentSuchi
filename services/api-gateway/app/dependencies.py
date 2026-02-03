from datetime import datetime, timezone

import jwt
from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.models.user import User
from app.services.user_service import find_or_create_user


async def get_current_user(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.removeprefix("Bearer ")

    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = await find_or_create_user(db, email=email)
    return user


def create_access_token(email: str) -> str:
    from datetime import timedelta

    exp = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiry_hours)
    payload = {"email": email, "exp": exp}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
