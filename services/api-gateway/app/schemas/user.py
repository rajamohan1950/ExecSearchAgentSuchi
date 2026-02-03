import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
