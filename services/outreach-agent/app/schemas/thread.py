import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MessageResponse(BaseModel):
    id: uuid.UUID
    thread_id: uuid.UUID
    direction: str
    from_email: str
    to_email: str
    subject: Optional[str]
    body_text: Optional[str]
    sentiment: Optional[str]
    llm_analysis: Optional[dict]
    sent_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class ThreadResponse(BaseModel):
    id: uuid.UUID
    contact_id: uuid.UUID
    contact_name: str = ""
    firm_name: str = ""
    gmail_thread_id: Optional[str]
    subject: Optional[str]
    status: str
    escalation_level: int
    strategy: str
    message_count: int = 0
    last_message_preview: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ThreadDetailResponse(ThreadResponse):
    messages: list[MessageResponse] = []
