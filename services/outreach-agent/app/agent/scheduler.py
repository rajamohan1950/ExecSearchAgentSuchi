"""APScheduler setup for the outreach agent.

Four recurring jobs:
1. check_inbox — every 15 minutes (configurable)
2. daily_briefing — every day at 9 AM IST
3. process_scheduled_tasks — every 5 minutes
4. scan_new_contacts — every 30 minutes (safety-net)
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from app.config import settings

logger = logging.getLogger(__name__)


def create_scheduler() -> AsyncIOScheduler:
    """Create APScheduler with database-backed job store for persistence."""
    # APScheduler needs a synchronous DB URL
    sync_db_url = settings.database_url.replace("+asyncpg", "").replace(
        "postgresql+asyncpg", "postgresql"
    )

    jobstores = {
        "default": SQLAlchemyJobStore(url=sync_db_url),
    }

    scheduler = AsyncIOScheduler(
        jobstores=jobstores,
        job_defaults={
            "coalesce": True,        # If multiple runs missed, run only once
            "max_instances": 1,       # Only one instance of each job at a time
            "misfire_grace_time": 300, # 5 min grace for missed jobs
        },
    )

    return scheduler


def setup_jobs(scheduler: AsyncIOScheduler):
    """Register all recurring jobs."""

    # 1. Check inbox every N minutes
    scheduler.add_job(
        "app.agent.jobs.check_inbox:check_inbox_job",
        "interval",
        minutes=settings.inbox_check_interval_minutes,
        id="check_inbox",
        replace_existing=True,
        name="Check Gmail inbox for responses",
    )
    logger.info(f"Scheduled: check_inbox every {settings.inbox_check_interval_minutes} min")

    # 2. Daily briefing at configured hour (IST)
    scheduler.add_job(
        "app.agent.jobs.daily_briefing:daily_briefing_job",
        "cron",
        hour=settings.daily_briefing_hour,
        minute=0,
        timezone=settings.daily_briefing_timezone,
        id="daily_briefing",
        replace_existing=True,
        name="Send daily briefing to Rajamohan",
    )
    logger.info(f"Scheduled: daily_briefing at {settings.daily_briefing_hour}:00 {settings.daily_briefing_timezone}")

    # 3. Process pending scheduled tasks every 5 minutes
    scheduler.add_job(
        "app.agent.jobs.process_tasks:process_scheduled_tasks_job",
        "interval",
        minutes=5,
        id="process_scheduled_tasks",
        replace_existing=True,
        name="Process pending outreach tasks",
    )
    logger.info("Scheduled: process_scheduled_tasks every 5 min")

    # 4. Safety-net: scan for new contacts without scheduled tasks (every 30 min)
    scheduler.add_job(
        "app.agent.jobs.scan_new_contacts:scan_new_contacts_job",
        "interval",
        minutes=30,
        id="scan_new_contacts",
        replace_existing=True,
        name="Safety-net scan for orphaned new contacts",
    )
    logger.info("Scheduled: scan_new_contacts every 30 min")
