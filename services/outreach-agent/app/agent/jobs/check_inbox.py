"""Job: Check Gmail inbox for new responses and process them."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.db.session import async_session_factory
from app.models.contact import OutreachContact
from app.models.thread import ConversationThread
from app.models.message import ConversationMessage
from app.services.gmail_service import gmail_service
from app.services.llm_service import llm_service
from app.services.action_logger import log_action
from app.agent.jobs.send_outreach import execute_outreach_for_contact

logger = logging.getLogger(__name__)

# Track last check time in memory (recovered from DB on restart)
_last_check_time: datetime = None


async def check_inbox_job():
    """
    Poll Gmail inbox for new messages, match them to contacts,
    analyze with LLM, and trigger agent responses.
    """
    global _last_check_time

    if _last_check_time is None:
        _last_check_time = datetime.now(timezone.utc) - timedelta(hours=1)

    logger.info(f"[INBOX CHECK] Checking for messages since {_last_check_time.isoformat()}")

    try:
        new_messages = await gmail_service.get_new_messages(since_timestamp=_last_check_time)
        _last_check_time = datetime.now(timezone.utc)

        if not new_messages:
            logger.info("[INBOX CHECK] No new messages")
            return

        logger.info(f"[INBOX CHECK] Found {len(new_messages)} new message(s)")

        async with async_session_factory() as db:
            for msg in new_messages:
                try:
                    await _process_inbound_message(db, msg)
                except Exception as e:
                    logger.error(f"[INBOX CHECK] Error processing message {msg.get('message_id')}: {e}")

    except Exception as e:
        logger.error(f"[INBOX CHECK] Job failed: {e}", exc_info=True)


async def _process_inbound_message(db, msg: dict):
    """Process a single inbound email — match to contact and analyze."""
    from_email = msg.get("from_email", "").lower().strip()
    gmail_thread_id = msg.get("thread_id")
    gmail_message_id = msg.get("message_id")

    if not from_email:
        return

    # Try to match by Gmail thread ID first
    contact = None
    thread = None

    if gmail_thread_id:
        result = await db.execute(
            select(ConversationThread)
            .options(
                selectinload(ConversationThread.contact).selectinload(OutreachContact.firm),
                selectinload(ConversationThread.messages),
            )
            .where(ConversationThread.gmail_thread_id == gmail_thread_id)
        )
        thread = result.scalar_one_or_none()
        if thread:
            contact = thread.contact

    # Fallback: match by sender email
    if not contact:
        result = await db.execute(
            select(OutreachContact)
            .options(selectinload(OutreachContact.firm))
            .where(func.lower(OutreachContact.email) == from_email)
        )
        contact = result.scalar_one_or_none()

    if not contact:
        logger.debug(f"[INBOX CHECK] No matching contact for {from_email} — skipping")
        return

    # Check if we already have this message
    result = await db.execute(
        select(ConversationMessage).where(
            ConversationMessage.gmail_message_id == gmail_message_id
        )
    )
    if result.scalar_one_or_none():
        logger.debug(f"[INBOX CHECK] Message {gmail_message_id} already stored — skipping")
        return

    logger.info(f"[INBOX CHECK] New response from {contact.name} ({from_email})")

    # Analyze the response with LLM
    thread_history = []
    if thread:
        thread_history = [
            {
                "direction": m.direction,
                "body_text": m.body_text or "",
                "subject": m.subject or "",
                "sent_at": m.sent_at.isoformat() if m.sent_at else "",
            }
            for m in (thread.messages or [])
        ]

    analysis = await llm_service.analyze_response(
        message_body=msg.get("body_text", ""),
        thread_context=thread_history,
    )

    # Create thread if doesn't exist
    if not thread:
        thread = ConversationThread(
            contact_id=contact.id,
            gmail_thread_id=gmail_thread_id,
            subject=msg.get("subject"),
        )
        db.add(thread)
        await db.flush()

    # Store the inbound message
    message = ConversationMessage(
        thread_id=thread.id,
        gmail_message_id=gmail_message_id,
        direction="inbound",
        from_email=from_email,
        to_email=msg.get("to_email", ""),
        subject=msg.get("subject"),
        body_text=msg.get("body_text"),
        sentiment=analysis.get("sentiment"),
        llm_analysis=analysis,
        sent_at=msg.get("received_at", datetime.now(timezone.utc)),
    )
    db.add(message)

    # Update contact status
    if contact.status in ("new", "contacted"):
        contact.status = "responded"
    elif contact.status == "responded":
        contact.status = "in_conversation"

    # Check interest level for conversion
    if analysis.get("interest_level") == "high":
        contact.status = "in_conversation"
        thread.status = "active"

    await db.commit()

    # Log the response
    await log_action(
        db,
        action_type="analyze_response",
        contact_id=contact.id,
        thread_id=thread.id,
        description=f"Received and analysed response from {contact.name}: {analysis.get('summary', '')}",
        output_data=analysis,
        llm_model_used="claude",
    )

    # Trigger agent to compose a reply
    logger.info(f"[INBOX CHECK] Triggering agent response for {contact.name}")
    try:
        await execute_outreach_for_contact(contact.id)
    except Exception as e:
        logger.error(f"[INBOX CHECK] Failed to trigger response for {contact.name}: {e}")
