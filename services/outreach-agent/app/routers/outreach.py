"""Outreach thread and conversation endpoints + manual agent triggers."""

import uuid
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.contact import OutreachContact
from app.models.thread import ConversationThread
from app.models.message import ConversationMessage
from app.models.firm import OutreachFirm
from app.schemas.thread import ThreadResponse, ThreadDetailResponse, MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/outreach", tags=["outreach"])


@router.get("/threads", response_model=list[ThreadResponse])
async def list_threads(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List all conversation threads with latest message preview."""
    query = (
        select(ConversationThread)
        .options(
            selectinload(ConversationThread.contact).selectinload(OutreachContact.firm),
            selectinload(ConversationThread.messages),
        )
    )

    if status:
        query = query.where(ConversationThread.status == status)

    query = query.order_by(ConversationThread.updated_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    threads = result.scalars().unique().all()

    response = []
    for t in threads:
        last_msg = t.messages[-1] if t.messages else None
        response.append(ThreadResponse(
            id=t.id,
            contact_id=t.contact_id,
            contact_name=t.contact.name if t.contact else "",
            firm_name=t.contact.firm.name if t.contact and t.contact.firm else "",
            gmail_thread_id=t.gmail_thread_id,
            subject=t.subject,
            status=t.status,
            escalation_level=t.escalation_level,
            strategy=t.strategy,
            message_count=len(t.messages),
            last_message_preview=last_msg.body_text[:200] if last_msg and last_msg.body_text else None,
            created_at=t.created_at,
            updated_at=t.updated_at,
        ))

    return response


@router.get("/threads/{thread_id}", response_model=ThreadDetailResponse)
async def get_thread_detail(
    thread_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get full thread with all messages."""
    result = await db.execute(
        select(ConversationThread)
        .options(
            selectinload(ConversationThread.contact).selectinload(OutreachContact.firm),
            selectinload(ConversationThread.messages),
        )
        .where(ConversationThread.id == thread_id)
    )
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    return ThreadDetailResponse(
        id=thread.id,
        contact_id=thread.contact_id,
        contact_name=thread.contact.name if thread.contact else "",
        firm_name=thread.contact.firm.name if thread.contact and thread.contact.firm else "",
        gmail_thread_id=thread.gmail_thread_id,
        subject=thread.subject,
        status=thread.status,
        escalation_level=thread.escalation_level,
        strategy=thread.strategy,
        message_count=len(thread.messages),
        created_at=thread.created_at,
        updated_at=thread.updated_at,
        messages=[MessageResponse.model_validate(m) for m in thread.messages],
    )


@router.post("/trigger/{contact_id}", status_code=202)
async def trigger_outreach(
    contact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger the agent to process a specific contact."""
    result = await db.execute(
        select(OutreachContact)
        .options(selectinload(OutreachContact.firm))
        .where(OutreachContact.id == contact_id)
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    # Trigger the agent graph asynchronously
    try:
        from app.agent.jobs.send_outreach import execute_outreach_for_contact
        import asyncio
        asyncio.create_task(execute_outreach_for_contact(contact_id))
        logger.info(f"Triggered outreach for contact {contact_id}")
    except Exception as e:
        logger.error(f"Failed to trigger outreach: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger outreach: {str(e)}")

    return {
        "status": "triggered",
        "contact_id": str(contact_id),
        "contact_name": contact.name,
        "firm_name": contact.firm.name if contact.firm else "Unknown",
    }


@router.get("/agent-status")
async def get_agent_status(db: AsyncSession = Depends(get_db)):
    """Get current agent status and next scheduled tasks."""
    from app.models.scheduled_task import AgentScheduledTask
    from app.models.action import AgentAction

    # Pending tasks count
    result = await db.execute(
        select(func.count()).select_from(AgentScheduledTask).where(
            AgentScheduledTask.status == "pending"
        )
    )
    pending_count = result.scalar() or 0

    # Next scheduled task
    result = await db.execute(
        select(AgentScheduledTask)
        .where(AgentScheduledTask.status == "pending")
        .order_by(AgentScheduledTask.scheduled_for.asc())
        .limit(1)
    )
    next_task = result.scalar_one_or_none()

    # Last action
    result = await db.execute(
        select(AgentAction)
        .order_by(AgentAction.created_at.desc())
        .limit(1)
    )
    last_action = result.scalar_one_or_none()

    # Check if scheduler is running
    try:
        from app.main import _scheduler
        scheduler_running = _scheduler is not None and _scheduler.running
    except Exception:
        scheduler_running = False

    return {
        "scheduler_running": scheduler_running,
        "pending_tasks": pending_count,
        "next_scheduled_task": next_task.scheduled_for.isoformat() if next_task else None,
        "last_action_type": last_action.action_type if last_action else None,
        "last_action_at": last_action.created_at.isoformat() if last_action else None,
    }
