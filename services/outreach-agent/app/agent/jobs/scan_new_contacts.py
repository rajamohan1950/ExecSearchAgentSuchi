"""Job: Safety-net scan for new contacts without scheduled tasks.

Catches contacts that slipped through without a send_initial task:
- Upload errors partway through task scheduling
- Contacts created via API without scheduling
- Any edge case where a 'new' contact has no pending task

Runs every 30 minutes via APScheduler.
"""

import logging

from sqlalchemy import select

from app.db.session import async_session_factory
from app.models.contact import OutreachContact
from app.models.scheduled_task import AgentScheduledTask
from app.services.task_scheduler import schedule_initial_tasks_for_contacts
from app.services.action_logger import log_action

logger = logging.getLogger(__name__)


async def scan_new_contacts_job():
    """
    Find contacts with status='new' that have no pending/running scheduled task,
    and create send_initial tasks for them.
    """
    async with async_session_factory() as db:
        try:
            # Subquery: contact IDs that already have a pending/running task
            pending_task_subquery = (
                select(AgentScheduledTask.contact_id).where(
                    AgentScheduledTask.status.in_(["pending", "running"]),
                    AgentScheduledTask.task_type.in_(["send_initial", "send_followup"]),
                )
            )

            # Find 'new' contacts NOT in that subquery
            result = await db.execute(
                select(OutreachContact.id)
                .where(
                    OutreachContact.status == "new",
                    ~OutreachContact.id.in_(pending_task_subquery),
                )
                .limit(100)  # Process max 100 at a time
            )
            orphan_contact_ids = [row[0] for row in result.all()]

            if not orphan_contact_ids:
                return  # Nothing to do — happy path

            logger.warning(
                f"[SCAN NEW] Found {len(orphan_contact_ids)} new contact(s) "
                f"without scheduled tasks — creating send_initial tasks"
            )

            tasks_created = await schedule_initial_tasks_for_contacts(
                db, orphan_contact_ids
            )
            await db.commit()

            if tasks_created > 0:
                await log_action(
                    db,
                    action_type="scan_new_contacts",
                    description=(
                        f"Safety-net scan found {len(orphan_contact_ids)} orphaned "
                        f"contacts, scheduled {tasks_created} initial outreach tasks"
                    ),
                )

            logger.info(
                f"[SCAN NEW] Scheduled {tasks_created} tasks for orphaned contacts"
            )

        except Exception as e:
            logger.error(f"[SCAN NEW] Job failed: {e}", exc_info=True)
