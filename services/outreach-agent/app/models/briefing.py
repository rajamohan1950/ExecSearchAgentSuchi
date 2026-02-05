import uuid
from datetime import date, datetime, timezone

from sqlalchemy import String, Date, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DailyBriefing(Base):
    __tablename__ = "daily_briefings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    briefing_date: Mapped[date] = mapped_column(Date, nullable=False, unique=True)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    stats: Mapped[dict] = mapped_column(JSONB, nullable=False)
    email_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    gmail_message_id: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
