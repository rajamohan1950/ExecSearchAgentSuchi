"""Job: Compose and send daily 9 AM briefing to Rajamohan."""

import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select, func

from app.db.session import async_session_factory
from app.models.contact import OutreachContact
from app.models.action import AgentAction
from app.models.briefing import DailyBriefing
from app.services.llm_service import llm_service
from app.services.gmail_service import gmail_service
from app.services.action_logger import log_action
from app.config import settings

logger = logging.getLogger(__name__)


async def daily_briefing_job():
    """
    Compose and send the daily morning briefing to Rajamohan.

    Runs at 9 AM IST every day via APScheduler.
    """
    today = date.today()
    logger.info(f"[DAILY BRIEFING] Generating briefing for {today}")

    async with async_session_factory() as db:
        try:
            # Check if already sent today
            result = await db.execute(
                select(DailyBriefing).where(DailyBriefing.briefing_date == today)
            )
            existing = result.scalar_one_or_none()
            if existing and existing.email_sent:
                logger.info("[DAILY BRIEFING] Already sent today — skipping")
                return

            # Gather today's stats
            stats = await _gather_stats(db)

            # Gather yesterday's stats for comparison
            yesterday_stats = await _gather_yesterday_stats(db)

            # Get notable events from last 24 hours
            notable_events = await _get_notable_events(db)

            # Compose briefing with LLM
            summary = await llm_service.compose_daily_briefing(
                stats=stats,
                yesterday_stats=yesterday_stats,
                notable_events=notable_events,
            )

            # Send email
            gmail_result = None
            if settings.rajamohan_email:
                gmail_result = await gmail_service.send_email(
                    to=settings.rajamohan_email,
                    subject=f"Suchi Daily Briefing — {today.strftime('%d %b %Y')}",
                    body_text=summary,
                    body_html=f"<div style='font-family: sans-serif; line-height: 1.6;'><pre>{summary}</pre></div>",
                )

            # Store briefing
            briefing = existing or DailyBriefing(briefing_date=today)
            briefing.summary_text = summary
            briefing.stats = stats
            briefing.email_sent = gmail_result is not None
            briefing.gmail_message_id = gmail_result.get("message_id") if gmail_result else None

            if not existing:
                db.add(briefing)
            await db.commit()

            await log_action(
                db,
                action_type="daily_briefing",
                description=f"Daily briefing for {today}: {summary[:100]}...",
                output_data={"stats": stats, "email_sent": briefing.email_sent},
            )

            logger.info(f"[DAILY BRIEFING] Sent for {today}")

        except Exception as e:
            logger.error(f"[DAILY BRIEFING] Failed: {e}", exc_info=True)
            try:
                await log_action(
                    db,
                    action_type="daily_briefing",
                    status="failed",
                    error_message=str(e),
                )
            except Exception:
                pass


async def _gather_stats(db) -> dict:
    """Gather current aggregate stats."""
    result = await db.execute(
        select(
            OutreachContact.status,
            func.count().label("count"),
        )
        .group_by(OutreachContact.status)
    )
    status_counts = {row.status: row.count for row in result.all()}

    from app.models.firm import OutreachFirm
    result = await db.execute(select(func.count()).select_from(OutreachFirm))
    total_firms = result.scalar() or 0

    return {
        "total_firms": total_firms,
        "total_contacts": sum(status_counts.values()),
        "not_contacted": status_counts.get("new", 0),
        "contacted": status_counts.get("contacted", 0),
        "responded": status_counts.get("responded", 0),
        "in_conversation": status_counts.get("in_conversation", 0),
        "converted": status_counts.get("converted", 0),
        "cold": status_counts.get("cold", 0),
    }


async def _gather_yesterday_stats(db) -> dict:
    """Gather stats from yesterday for comparison."""
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    yesterday_start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)

    # Yesterday's briefing stats (if exists)
    result = await db.execute(
        select(DailyBriefing).where(DailyBriefing.briefing_date == yesterday.date())
    )
    yesterday_briefing = result.scalar_one_or_none()
    if yesterday_briefing and yesterday_briefing.stats:
        return {
            **yesterday_briefing.stats,
            "new_responses": 0,  # Will be calculated below
        }

    # Count new responses since yesterday
    from app.models.message import ConversationMessage
    result = await db.execute(
        select(func.count()).select_from(ConversationMessage).where(
            ConversationMessage.direction == "inbound",
            ConversationMessage.created_at >= yesterday_start,
        )
    )
    new_responses = result.scalar() or 0

    return {
        "contacted": 0,
        "new_responses": new_responses,
    }


async def _get_notable_events(db) -> list[dict]:
    """Get notable agent actions from the last 24 hours."""
    since = datetime.now(timezone.utc) - timedelta(hours=24)

    result = await db.execute(
        select(AgentAction)
        .where(
            AgentAction.created_at >= since,
            AgentAction.action_type.in_([
                "analyze_response", "mark_cold", "mark_converted", "error",
            ]),
        )
        .order_by(AgentAction.created_at.desc())
        .limit(10)
    )
    actions = result.scalars().all()

    return [
        {
            "type": a.action_type,
            "description": a.description or "",
            "timestamp": a.created_at.isoformat(),
        }
        for a in actions
    ]
