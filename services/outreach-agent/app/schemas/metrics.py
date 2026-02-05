import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class OutreachMetrics(BaseModel):
    total_firms: int = 0
    total_contacts: int = 0
    not_contacted: int = 0
    contacted: int = 0
    responded: int = 0
    in_conversation: int = 0
    converted: int = 0
    cold: int = 0
    emails_sent_today: int = 0
    emails_sent_total: int = 0
    response_rate_percent: float = 0.0


class AgentActionResponse(BaseModel):
    id: uuid.UUID
    contact_id: Optional[uuid.UUID]
    action_type: str
    description: Optional[str]
    llm_model_used: Optional[str]
    status: str
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AgentStatus(BaseModel):
    scheduler_running: bool = False
    last_inbox_check: Optional[datetime] = None
    last_outreach_sent: Optional[datetime] = None
    pending_tasks: int = 0
    next_scheduled_task: Optional[datetime] = None


class DailyBriefingResponse(BaseModel):
    id: uuid.UUID
    briefing_date: date
    summary_text: str
    stats: dict
    email_sent: bool
    created_at: datetime

    class Config:
        from_attributes = True
