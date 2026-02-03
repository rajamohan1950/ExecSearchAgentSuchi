import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, Boolean, Text, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ProfileVersion(Base):
    __tablename__ = "profile_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="linkedin_pdf")
    source_filename: Mapped[str | None] = mapped_column(String(255))

    headline: Mapped[str | None] = mapped_column(String(500))
    summary: Mapped[str | None] = mapped_column(Text)
    experience: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    education: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    skills: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    certifications: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    languages: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    volunteer: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    patents: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    publications: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    awards: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    projects: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    courses: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    raw_parsed_data: Mapped[dict | None] = mapped_column(JSONB)

    pdf_storage_key: Mapped[str | None] = mapped_column(String(500))
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="profile_versions")

    __table_args__ = (
        UniqueConstraint("user_id", "version", name="uq_user_version"),
        Index("idx_profile_versions_user_id", "user_id"),
        Index("idx_profile_versions_current", "user_id", "is_current", postgresql_where=(is_current == True)),
    )
