import uuid
from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel


class ProfileUploadResponse(BaseModel):
    profile_version_id: uuid.UUID
    version: int
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    website_url: Optional[str] = None
    headline: Optional[str] = None
    summary: Optional[str] = None
    experience: list[Any] = []
    education: list[Any] = []
    skills: list[str] = []
    skill_categories: list[Any] = []
    certifications: list[Any] = []
    languages: list[Any] = []
    volunteer: list[Any] = []
    patents: list[Any] = []
    publications: list[Any] = []
    awards: list[Any] = []
    projects: list[Any] = []
    courses: list[Any] = []
    total_experience_years: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ProfileVersionSummary(BaseModel):
    id: uuid.UUID
    version: int
    source_type: str
    source_filename: Optional[str] = None
    headline: Optional[str] = None
    is_current: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ProfileVersionDetail(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    version: int
    source_type: str
    source_filename: Optional[str] = None
    headline: Optional[str] = None
    summary: Optional[str] = None
    experience: list[Any] = []
    education: list[Any] = []
    skills: list[str] = []
    skill_categories: list[Any] = []
    certifications: list[Any] = []
    languages: list[Any] = []
    volunteer: list[Any] = []
    patents: list[Any] = []
    publications: list[Any] = []
    awards: list[Any] = []
    projects: list[Any] = []
    courses: list[Any] = []
    pdf_storage_key: Optional[str] = None
    is_current: bool
    created_at: datetime
    raw_parsed_data: Optional[dict] = None

    class Config:
        from_attributes = True


class ProfileVersionList(BaseModel):
    versions: list[ProfileVersionSummary]


class DashboardStats(BaseModel):
    total_resumes_uploaded: int = 0
    days_since_last_update: Optional[int] = None
    current_version: Optional[int] = None
    total_experience_years: Optional[int] = None
    total_skills: int = 0
    total_roles: int = 0
    profile_completeness: int = 0  # percentage
