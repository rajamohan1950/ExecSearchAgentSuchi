import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


# ── Contacts ──────────────────────────────────────────────

class ContactCreate(BaseModel):
    name: str
    email: EmailStr
    title: Optional[str] = None
    phone: Optional[str] = None
    is_primary: bool = False


class ContactResponse(BaseModel):
    id: uuid.UUID
    firm_id: uuid.UUID
    name: str
    email: str
    title: Optional[str]
    phone: Optional[str]
    is_primary: bool
    status: str
    last_contacted_at: Optional[datetime]
    next_followup_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Firms ─────────────────────────────────────────────────

class FirmCreate(BaseModel):
    name: str
    website: Optional[str] = None
    industry_focus: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    contacts: list[ContactCreate] = []


class FirmResponse(BaseModel):
    id: uuid.UUID
    name: str
    website: Optional[str]
    industry_focus: Optional[str]
    location: Optional[str]
    notes: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    contacts: list[ContactResponse] = []

    class Config:
        from_attributes = True


class FirmListItem(BaseModel):
    id: uuid.UUID
    name: str
    website: Optional[str]
    industry_focus: Optional[str]
    location: Optional[str]
    status: str
    contact_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class BulkUploadResponse(BaseModel):
    firms_created: int
    contacts_created: int
    tasks_scheduled: int = 0
    errors: list[str] = []


class FirmUpdate(BaseModel):
    name: Optional[str] = None
    website: Optional[str] = None
    industry_focus: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
