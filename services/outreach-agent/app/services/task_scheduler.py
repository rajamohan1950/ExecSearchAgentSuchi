"""Service: schedule initial outreach tasks for new contacts.

Used by:
- firm_service.bulk_upload() — immediately after CSV import
- scan_new_contacts_job() — safety-net for orphaned contacts
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scheduled_task import AgentScheduledTask
from app.config import settings

logger = logging.getLogger(__name__)


async def schedule_initial_tasks_for_contacts(
    db: AsyncSession,
    contact_ids: Sequence[uuid.UUID],
    start_from: datetime | None = None,
) -> int:
    """
    Create 'send_initial' scheduled tasks for a list of contacts,
    staggered to respect max_daily_outreach.

    Returns the number of tasks created.

    Staggering logic:
    - max_daily_outreach (default 20) contacts per day
    - Within each day, spread tasks across business hours (9 AM - 5 PM UTC)
    - ~20 contacts / 8 hours = 1 every 24 minutes within a day
    """
    if not contact_ids:
        return 0

    max_per_day = settings.max_daily_outreach
    if start_from is None:
        # Start 10 minutes from now to give the upload response time to return
        start_from = datetime.now(timezone.utc) + timedelta(minutes=10)

    # ── Filter out contacts that already have a pending/running send_initial task ──
    existing_result = await db.execute(
        select(AgentScheduledTask.contact_id).where(
            AgentScheduledTask.contact_id.in_(contact_ids),
            AgentScheduledTask.task_type == "send_initial",
            AgentScheduledTask.status.in_(["pending", "running"]),
        )
    )
    already_scheduled = {row[0] for row in existing_result.all()}

    to_schedule = [cid for cid in contact_ids if cid not in already_scheduled]

    if not to_schedule:
        logger.info("[TASK SCHEDULER] All contacts already have pending tasks")
        return 0

    # ── Count how many send_initial tasks are already scheduled for today ──
    today_start = start_from.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    existing_today_result = await db.execute(
        select(func.count())
        .select_from(AgentScheduledTask)
        .where(
            AgentScheduledTask.task_type == "send_initial",
            AgentScheduledTask.status.in_(["pending", "running"]),
            AgentScheduledTask.scheduled_for >= today_start,
            AgentScheduledTask.scheduled_for < today_end,
        )
    )
    already_today = existing_today_result.scalar() or 0

    # ── Stagger tasks across days, within business hours ──
    tasks_created = 0
    current_day_offset = 0
    slot_in_day = already_today  # Start after existing tasks for today

    # Interval between tasks within a day (business hours: 9:00 - 17:00 = 480 min)
    interval_minutes = max(480 // max(max_per_day, 1), 5)  # At least 5 min gap

    for contact_id in to_schedule:
        if slot_in_day >= max_per_day:
            current_day_offset += 1
            slot_in_day = 0

        # Business hours base: 9:00 AM UTC of the target day
        day_base = start_from + timedelta(days=current_day_offset)
        day_start = day_base.replace(hour=9, minute=0, second=0, microsecond=0)

        # For day 0, if start_from is already past 9 AM, use start_from
        if current_day_offset == 0 and start_from > day_start:
            day_start = start_from

        scheduled_for = day_start + timedelta(minutes=slot_in_day * interval_minutes)

        task = AgentScheduledTask(
            contact_id=contact_id,
            task_type="send_initial",
            scheduled_for=scheduled_for,
            payload={"source": "auto_schedule", "escalation_level": 0},
        )
        db.add(task)
        tasks_created += 1
        slot_in_day += 1

    await db.flush()
    logger.info(
        f"[TASK SCHEDULER] Scheduled {tasks_created} send_initial tasks "
        f"across {current_day_offset + 1} day(s) for {len(to_schedule)} contacts"
    )
    return tasks_created
