"""Metrics and analytics endpoints for the outreach dashboard."""

import logging
from datetime import datetime, timedelta, timezone, date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.contact import OutreachContact
from app.models.firm import OutreachFirm
from app.models.message import ConversationMessage
from app.models.action import AgentAction
from app.models.briefing import DailyBriefing
from app.schemas.metrics import (
    OutreachMetrics,
    AgentActionResponse,
    DailyBriefingResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/summary", response_model=OutreachMetrics)
async def get_metrics_summary(db: AsyncSession = Depends(get_db)):
    """Get aggregate outreach metrics for the dashboard."""
    # Total firms
    result = await db.execute(select(func.count()).select_from(OutreachFirm))
    total_firms = result.scalar() or 0

    # Contact status breakdown
    result = await db.execute(
        select(
            OutreachContact.status,
            func.count().label("count"),
        )
        .group_by(OutreachContact.status)
    )
    status_counts = {row.status: row.count for row in result.all()}

    total_contacts = sum(status_counts.values())
    not_contacted = status_counts.get("new", 0)
    contacted = status_counts.get("contacted", 0)
    responded = status_counts.get("responded", 0)
    in_conversation = status_counts.get("in_conversation", 0)
    converted = status_counts.get("converted", 0)
    cold = status_counts.get("cold", 0)

    # Emails sent today
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(func.count()).select_from(ConversationMessage).where(
            ConversationMessage.direction == "outbound",
            ConversationMessage.sent_at >= today_start,
        )
    )
    emails_sent_today = result.scalar() or 0

    # Total emails sent
    result = await db.execute(
        select(func.count()).select_from(ConversationMessage).where(
            ConversationMessage.direction == "outbound",
        )
    )
    emails_sent_total = result.scalar() or 0

    # Response rate
    response_rate = 0.0
    total_reached = contacted + responded + in_conversation + converted + cold
    if total_reached > 0:
        response_rate = round(((responded + in_conversation + converted) / total_reached) * 100, 1)

    return OutreachMetrics(
        total_firms=total_firms,
        total_contacts=total_contacts,
        not_contacted=not_contacted,
        contacted=contacted,
        responded=responded,
        in_conversation=in_conversation,
        converted=converted,
        cold=cold,
        emails_sent_today=emails_sent_today,
        emails_sent_total=emails_sent_total,
        response_rate_percent=response_rate,
    )


@router.get("/actions", response_model=list[AgentActionResponse])
async def get_agent_actions(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    action_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get recent agent actions (audit log)."""
    query = select(AgentAction)

    if action_type:
        query = query.where(AgentAction.action_type == action_type)

    query = query.order_by(AgentAction.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    actions = result.scalars().all()
    return [AgentActionResponse.model_validate(a) for a in actions]


@router.get("/briefings", response_model=list[DailyBriefingResponse])
async def get_daily_briefings(
    limit: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """Get daily briefing history."""
    result = await db.execute(
        select(DailyBriefing)
        .order_by(DailyBriefing.briefing_date.desc())
        .limit(limit)
    )
    briefings = result.scalars().all()
    return [DailyBriefingResponse.model_validate(b) for b in briefings]
