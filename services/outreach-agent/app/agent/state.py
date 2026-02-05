"""Agent state definitions for LangGraph."""

import uuid
from typing import Optional, TypedDict


class AgentState(TypedDict):
    """State maintained across a single agent loop iteration."""

    # Identity
    contact_id: uuid.UUID
    contact_name: str
    contact_email: str
    contact_title: str
    firm_name: str

    # Current status
    current_status: str  # new | contacted | responded | in_conversation | converted | cold
    escalation_level: int
    strategy: str
    days_since_last_contact: int

    # Thread context
    thread_id: Optional[uuid.UUID]
    gmail_thread_id: Optional[str]
    thread_history: list[dict]

    # Inbound message (if any)
    new_inbound_message: Optional[dict]

    # Agent decisions (populated during loop)
    action_decided: Optional[str]
    action_reasoning: Optional[str]
    email_composed: Optional[dict]  # {subject, body_text, body_html}
    analysis_result: Optional[dict]

    # Execution results
    send_result: Optional[dict]
    error: Optional[str]
