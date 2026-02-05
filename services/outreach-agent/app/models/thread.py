import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ConversationThread(Base):
    __tablename__ = "conversation_threads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("outreach_contacts.id", ondelete="CASCADE"), nullable=False
    )
    gmail_thread_id: Mapped[str | None] = mapped_column(String(255))
    subject: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    escalation_level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    strategy: Mapped[str] = mapped_column(String(100), nullable=False, default="standard")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    contact: Mapped["OutreachContact"] = relationship(back_populates="threads")
    messages: Mapped[list["ConversationMessage"]] = relationship(
        back_populates="thread", cascade="all, delete-orphan", order_by="ConversationMessage.sent_at"
    )
