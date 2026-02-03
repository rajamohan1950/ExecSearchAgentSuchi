import uuid

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.profile import (
    ProfileUploadResponse,
    ProfileVersionDetail,
    ProfileVersionList,
    ProfileVersionSummary,
    DashboardStats,
)
from app.services.profile_service import (
    upload_profile,
    get_current_profile,
    get_all_versions,
    get_version_by_id,
    get_dashboard_stats,
)

router = APIRouter(prefix="/profiles", tags=["profiles"])

MAX_PDF_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/upload", response_model=ProfileUploadResponse)
async def upload_linkedin_pdf(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    contents = await file.read()
    if len(contents) > MAX_PDF_SIZE:
        raise HTTPException(status_code=400, detail="PDF exceeds 10MB limit")
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        version, parsed = await upload_profile(db, user, contents, file.filename)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Profile parsing failed: {str(e)}")

    return ProfileUploadResponse(
        profile_version_id=version.id,
        version=version.version,
        name=parsed.get("name"),
        email=parsed.get("email"),
        phone=parsed.get("phone"),
        location=parsed.get("location"),
        linkedin_url=parsed.get("linkedin_url"),
        website_url=parsed.get("website_url"),
        headline=version.headline,
        summary=version.summary,
        experience=version.experience,
        education=version.education,
        skills=version.skills,
        skill_categories=parsed.get("skill_categories", []),
        certifications=version.certifications,
        languages=version.languages,
        volunteer=version.volunteer,
        patents=parsed.get("patents", []),
        publications=version.publications,
        awards=version.awards,
        projects=version.projects,
        courses=version.courses,
        total_experience_years=parsed.get("total_experience_years"),
        created_at=version.created_at,
    )


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stats = await get_dashboard_stats(db, user.id)
    return DashboardStats(**stats)


@router.get("/current", response_model=ProfileVersionDetail)
async def get_current(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await get_current_profile(db, user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="No profile found")
    return profile


@router.get("/versions", response_model=ProfileVersionList)
async def list_versions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    versions = await get_all_versions(db, user.id)
    return ProfileVersionList(versions=[ProfileVersionSummary.model_validate(v) for v in versions])


@router.get("/versions/{version_id}", response_model=ProfileVersionDetail)
async def get_version(
    version_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    version = await get_version_by_id(db, user.id, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return version
