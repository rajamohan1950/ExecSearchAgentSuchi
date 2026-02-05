"""Job: Send outreach email to a contact using the agent graph."""

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.db.session import async_session_factory
from app.models.contact import OutreachContact
from app.models.thread import ConversationThread
from app.models.message import ConversationMessage
from app.models.scheduled_task import AgentScheduledTask
from app.agent.graph import agent_graph
from app.agent.state import AgentState
from app.agent.escalation import get_days_until_next_followup, get_strategy_for_level
from app.services.action_logger import log_action

logger = logging.getLogger(__name__)


async def execute_outreach_for_contact(contact_id: uuid.UUID):
    """
    Execute the full agent graph for a single contact.

    This is called by:
    1. The scheduler (process_tasks job)
    2. Manual trigger via API
    """
    async with async_session_factory() as db:
        try:
            # Load contact with firm
            result = await db.execute(
                select(OutreachContact)
                .options(selectinload(OutreachContact.firm))
                .where(OutreachContact.id == contact_id)
            )
            contact = result.scalar_one_or_none()
            if not contact:
                logger.warning(f"Contact {contact_id} not found")
                return

            if contact.status in ("cold", "converted"):
                logger.info(f"Skipping {contact.name} — status is {contact.status}")
                return

            # Load existing thread and history
            result = await db.execute(
                select(ConversationThread)
                .options(selectinload(ConversationThread.messages))
                .where(ConversationThread.contact_id == contact_id)
                .order_by(ConversationThread.created_at.desc())
                .limit(1)
            )
            thread = result.scalar_one_or_none()

            thread_history = []
            gmail_thread_id = None
            escalation_level = 0

            if thread:
                gmail_thread_id = thread.gmail_thread_id
                escalation_level = thread.escalation_level
                thread_history = [
                    {
                        "direction": m.direction,
                        "body_text": m.body_text or "",
                        "subject": m.subject or "",
                        "sent_at": m.sent_at.isoformat() if m.sent_at else "",
                        "sentiment": m.sentiment,
                    }
                    for m in (thread.messages or [])
                ]

            # Calculate days since last contact
            days_since = 0
            if contact.last_contacted_at:
                delta = datetime.now(timezone.utc) - contact.last_contacted_at
                days_since = delta.days

            # Build initial state
            initial_state: AgentState = {
                "contact_id": contact.id,
                "contact_name": contact.name,
                "contact_email": contact.email,
                "contact_title": contact.title or "",
                "firm_name": contact.firm.name if contact.firm else "Unknown",
                "current_status": contact.status,
                "escalation_level": escalation_level,
                "strategy": get_strategy_for_level(escalation_level),
                "days_since_last_contact": days_since,
                "thread_id": thread.id if thread else None,
                "gmail_thread_id": gmail_thread_id,
                "thread_history": thread_history,
                "new_inbound_message": None,
                "action_decided": None,
                "action_reasoning": None,
                "email_composed": None,
                "analysis_result": None,
                "send_result": None,
                "error": None,
            }

            # Run the agent graph
            logger.info(f"Running agent graph for {contact.name} ({contact.email})")
            final_state = await agent_graph.ainvoke(initial_state)

            # Process results
            action = final_state.get("action_decided", "skip")
            send_result = final_state.get("send_result")
            email_composed = final_state.get("email_composed")
            error = final_state.get("error")

            if action == "mark_cold":
                contact.status = "cold"
                await db.commit()
                await log_action(
                    db,
                    action_type="mark_cold",
                    contact_id=contact.id,
                    description=f"Marked {contact.name} as cold — {final_state.get('action_reasoning', '')}",
                )
                return

            if action in ("skip", "wait"):
                await log_action(
                    db,
                    action_type=action,
                    contact_id=contact.id,
                    description=final_state.get("action_reasoning", ""),
                )
                return

            if send_result and email_composed:
                # Create or update thread
                if not thread:
                    thread = ConversationThread(
                        contact_id=contact.id,
                        gmail_thread_id=send_result.get("thread_id"),
                        subject=email_composed.get("subject"),
                        strategy=final_state.get("strategy", "standard"),
                    )
                    db.add(thread)
                    await db.flush()
                else:
                    thread.gmail_thread_id = send_result.get("thread_id") or thread.gmail_thread_id
                    thread.escalation_level = escalation_level + 1
                    thread.strategy = final_state.get("strategy", thread.strategy)

                # Store outbound message
                message = ConversationMessage(
                    thread_id=thread.id,
                    gmail_message_id=send_result.get("message_id"),
                    direction="outbound",
                    from_email=f"suchi@agent",
                    to_email=contact.email,
                    subject=email_composed.get("subject"),
                    body_text=email_composed.get("body_text"),
                    body_html=email_composed.get("body_html"),
                )
                db.add(message)

                # Update contact status
                contact.status = "contacted" if contact.status == "new" else contact.status
                contact.last_contacted_at = datetime.now(timezone.utc)

                # Schedule next follow-up
                next_days = get_days_until_next_followup(escalation_level)
                if next_days:
                    contact.next_followup_at = datetime.now(timezone.utc) + timedelta(days=next_days)
                    task = AgentScheduledTask(
                        contact_id=contact.id,
                        task_type="send_followup",
                        scheduled_for=contact.next_followup_at,
                        payload={"escalation_level": escalation_level + 1},
                    )
                    db.add(task)

                await db.commit()

                await log_action(
                    db,
                    action_type=f"send_{action.replace('send_', '')}",
                    contact_id=contact.id,
                    thread_id=thread.id,
                    description=f"Sent {action} to {contact.name} at {contact.firm.name if contact.firm else 'Unknown'}",
                    output_data={
                        "subject": email_composed.get("subject"),
                        "gmail_message_id": send_result.get("message_id"),
                    },
                    llm_model_used="claude",
                )

                logger.info(f"Outreach completed for {contact.name}")

            elif error:
                await log_action(
                    db,
                    action_type="error",
                    contact_id=contact.id,
                    description=f"Agent error for {contact.name}",
                    status="failed",
                    error_message=error,
                )

        except Exception as e:
            logger.error(f"Agent execution failed for contact {contact_id}: {e}", exc_info=True)
            try:
                await log_action(
                    db,
                    action_type="error",
                    contact_id=contact_id,
                    description="Unhandled agent error",
                    status="failed",
                    error_message=str(e),
                )
            except Exception:
                pass
