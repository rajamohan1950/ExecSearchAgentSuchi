import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile_version import ProfileVersion
from app.models.user import User
from app.services.storage_service import storage_service
from app.services.parser_client import parse_linkedin_pdf
from app.services.user_service import update_user

logger = logging.getLogger(__name__)


async def upload_profile(
    db: AsyncSession,
    user: User,
    pdf_bytes: bytes,
    filename: str,
) -> tuple["ProfileVersion", dict]:
    """Upload and parse LinkedIn PDF. Returns (profile_version, parsed_data)."""

    # 1. Get next version number
    result = await db.execute(
        select(func.coalesce(func.max(ProfileVersion.version), 0))
        .where(ProfileVersion.user_id == user.id)
    )
    current_max = result.scalar()
    next_version = current_max + 1

    # 2. Upload PDF to storage
    storage_key = storage_service.upload_pdf(
        user_id=str(user.id),
        version=next_version,
        file_bytes=pdf_bytes,
        filename=filename,
    )

    # 3. Parse PDF via parser service
    parsed = await parse_linkedin_pdf(pdf_bytes, filename)

    # 4. Mark all existing versions as not current
    await db.execute(
        update(ProfileVersion)
        .where(ProfileVersion.user_id == user.id, ProfileVersion.is_current == True)
        .values(is_current=False)
    )

    # 5. Create new profile version
    profile_version = ProfileVersion(
        user_id=user.id,
        version=next_version,
        source_type="linkedin_pdf",
        source_filename=filename,
        headline=parsed.get("headline"),
        summary=parsed.get("summary"),
        experience=parsed.get("experience", []),
        education=parsed.get("education", []),
        skills=parsed.get("skills", []),
        certifications=parsed.get("certifications", []),
        languages=parsed.get("languages", []),
        volunteer=parsed.get("volunteer", []),
        patents=parsed.get("patents", []),
        publications=parsed.get("publications", []),
        awards=parsed.get("awards", []),
        projects=parsed.get("projects", []),
        courses=parsed.get("courses", []),
        raw_parsed_data=parsed,
        pdf_storage_key=storage_key,
        is_current=True,
    )
    db.add(profile_version)

    # 6. Update user fields from parsed data (always update, not just when empty)
    update_fields = {}
    if parsed.get("name"):
        update_fields["name"] = parsed["name"]
    if parsed.get("phone"):
        update_fields["phone"] = parsed["phone"]
    if parsed.get("location"):
        update_fields["location"] = parsed["location"]
    if parsed.get("linkedin_url"):
        update_fields["linkedin_url"] = parsed["linkedin_url"]

    if update_fields:
        await update_user(db, user, **update_fields)

    await db.commit()
    await db.refresh(profile_version)
    return profile_version, parsed


async def get_current_profile(db: AsyncSession, user_id: uuid.UUID) -> ProfileVersion | None:
    result = await db.execute(
        select(ProfileVersion)
        .where(ProfileVersion.user_id == user_id, ProfileVersion.is_current == True)
    )
    return result.scalar_one_or_none()


async def get_all_versions(db: AsyncSession, user_id: uuid.UUID) -> list[ProfileVersion]:
    result = await db.execute(
        select(ProfileVersion)
        .where(ProfileVersion.user_id == user_id)
        .order_by(ProfileVersion.version.desc())
    )
    return list(result.scalars().all())


async def get_version_by_id(
    db: AsyncSession, user_id: uuid.UUID, version_id: uuid.UUID
) -> ProfileVersion | None:
    result = await db.execute(
        select(ProfileVersion)
        .where(ProfileVersion.id == version_id, ProfileVersion.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_dashboard_stats(db: AsyncSession, user_id: uuid.UUID) -> dict:
    """Calculate dashboard statistics for a user."""
    versions = await get_all_versions(db, user_id)

    if not versions:
        return {
            "total_resumes_uploaded": 0,
            "days_since_last_update": None,
            "current_version": None,
            "total_experience_years": None,
            "total_skills": 0,
            "total_roles": 0,
            "profile_completeness": 0,
        }

    current = next((v for v in versions if v.is_current), versions[0])
    now = datetime.now(timezone.utc)
    last_upload = current.created_at
    if last_upload.tzinfo is None:
        from datetime import timezone as tz
        last_upload = last_upload.replace(tzinfo=tz.utc)
    days_since = (now - last_upload).days

    # Profile completeness
    sections_present = 0
    total_sections = 7  # headline, summary, experience, education, skills, languages, certifications
    if current.headline:
        sections_present += 1
    if current.summary:
        sections_present += 1
    if current.experience:
        sections_present += 1
    if current.education:
        sections_present += 1
    if current.skills:
        sections_present += 1
    if current.languages:
        sections_present += 1
    if current.certifications:
        sections_present += 1

    completeness = int((sections_present / total_sections) * 100)

    # Total experience years from raw_parsed_data
    total_exp_years = None
    if current.raw_parsed_data:
        total_exp_years = current.raw_parsed_data.get("total_experience_years")

    return {
        "total_resumes_uploaded": len(versions),
        "days_since_last_update": days_since,
        "current_version": current.version,
        "total_experience_years": total_exp_years,
        "total_skills": len(current.skills) if current.skills else 0,
        "total_roles": len(current.experience) if current.experience else 0,
        "profile_completeness": completeness,
    }
