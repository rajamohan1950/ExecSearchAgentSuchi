"""Audit logger for all agent decisions and actions."""

import logging
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action import AgentAction

logger = logging.getLogger(__name__)


async def log_action(
    db: AsyncSession,
    action_type: str,
    contact_id: Optional[uuid.UUID] = None,
    thread_id: Optional[uuid.UUID] = None,
    description: Optional[str] = None,
    input_data: Optional[dict] = None,
    output_data: Optional[dict] = None,
    llm_model_used: Optional[str] = None,
    llm_tokens_used: Optional[int] = None,
    status: str = "completed",
    error_message: Optional[str] = None,
) -> AgentAction:
    """Log an agent action to the audit trail."""
    try:
        action = AgentAction(
            contact_id=contact_id,
            thread_id=thread_id,
            action_type=action_type,
            description=description,
            input_data=input_data,
            output_data=output_data,
            llm_model_used=llm_model_used,
            llm_tokens_used=llm_tokens_used,
            status=status,
            error_message=error_message,
        )
        db.add(action)
        await db.commit()
        await db.refresh(action)

        logger.info(
            f"[AGENT ACTION] {action_type} | contact={contact_id} | status={status}"
            f"{f' | error={error_message}' if error_message else ''}"
        )
        return action

    except Exception as e:
        logger.error(f"Failed to log agent action: {e}")
        # Don't let logging failures crash the agent
        try:
            await db.rollback()
        except Exception:
            pass
        return None
