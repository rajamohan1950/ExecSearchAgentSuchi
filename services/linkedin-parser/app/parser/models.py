from pydantic import BaseModel
from typing import Optional


class ExperienceEntry(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[str] = None


class EducationEntry(BaseModel):
    school: str
    degree: Optional[str] = None
    field: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class CertificationEntry(BaseModel):
    name: str
    authority: Optional[str] = None
    date: Optional[str] = None


class LanguageEntry(BaseModel):
    language: str
    proficiency: Optional[str] = None


class VolunteerEntry(BaseModel):
    role: str
    organization: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None


class PublicationEntry(BaseModel):
    title: str
    publisher: Optional[str] = None
    date: Optional[str] = None
    description: Optional[str] = None


class AwardEntry(BaseModel):
    title: str
    issuer: Optional[str] = None
    date: Optional[str] = None
    description: Optional[str] = None


class ProjectEntry(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class CourseEntry(BaseModel):
    name: str
    institution: Optional[str] = None


class PatentEntry(BaseModel):
    title: str
    patent_number: Optional[str] = None
    date: Optional[str] = None
    description: Optional[str] = None


class SkillCategory(BaseModel):
    category: str
    skills: list[str]


class ParsedProfile(BaseModel):
    # Contact info
    name: Optional[str] = None
    headline: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    website_url: Optional[str] = None

    # Sections
    summary: Optional[str] = None
    experience: list[ExperienceEntry] = []
    education: list[EducationEntry] = []
    skills: list[str] = []
    skill_categories: list[SkillCategory] = []
    certifications: list[CertificationEntry] = []
    languages: list[LanguageEntry] = []
    volunteer: list[VolunteerEntry] = []
    publications: list[PublicationEntry] = []
    awards: list[AwardEntry] = []
    patents: list[PatentEntry] = []
    projects: list[ProjectEntry] = []
    courses: list[CourseEntry] = []

    # Metadata
    total_experience_years: Optional[int] = None
    raw_text: Optional[str] = None
