"""Job: Process pending scheduled tasks from the database."""

import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.db.session import async_session_factory
from app.models.scheduled_task import AgentScheduledTask
from app.agent.jobs.send_outreach import execute_outreach_for_contact
from app.services.action_logger import log_action

logger = logging.getLogger(__name__)


async def process_scheduled_tasks_job():
    """
    Process all pending scheduled tasks that are due.

    Runs every 5 minutes via APScheduler.
    """
    now = datetime.now(timezone.utc)

    async with async_session_factory() as db:
        try:
            # Fetch all pending tasks that are due
            result = await db.execute(
                select(AgentScheduledTask)
                .where(
                    AgentScheduledTask.status == "pending",
                    AgentScheduledTask.scheduled_for <= now,
                )
                .order_by(AgentScheduledTask.scheduled_for.asc())
                .limit(20)  # Process max 20 at a time to avoid overload
            )
            tasks = result.scalars().all()

            if not tasks:
                return

            logger.info(f"[PROCESS TASKS] Processing {len(tasks)} pending task(s)")

            for task in tasks:
                try:
                    task.status = "running"
                    await db.commit()

                    if task.task_type in ("send_initial", "send_followup"):
                        if task.contact_id:
                            await execute_outreach_for_contact(task.contact_id)
                    else:
                        logger.warning(f"[PROCESS TASKS] Unknown task type: {task.task_type}")

                    task.status = "completed"
                    task.executed_at = datetime.now(timezone.utc)
                    await db.commit()

                    logger.info(f"[PROCESS TASKS] Completed task {task.id} ({task.task_type})")

                except Exception as e:
                    logger.error(f"[PROCESS TASKS] Task {task.id} failed: {e}")
                    task.retry_count += 1

                    if task.retry_count >= task.max_retries:
                        task.status = "failed"
                        task.error_message = str(e)
                        logger.warning(f"[PROCESS TASKS] Task {task.id} exhausted retries")
                    else:
                        task.status = "pending"  # Will retry on next cycle
                        task.error_message = f"Retry {task.retry_count}: {str(e)}"

                    await db.commit()

                    await log_action(
                        db,
                        action_type="task_error",
                        contact_id=task.contact_id,
                        description=f"Scheduled task {task.task_type} failed (attempt {task.retry_count})",
                        status="failed",
                        error_message=str(e),
                    )

        except Exception as e:
            logger.error(f"[PROCESS TASKS] Job failed: {e}", exc_info=True)
