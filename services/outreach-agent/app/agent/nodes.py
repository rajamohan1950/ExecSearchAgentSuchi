"""LangGraph node functions for the autonomous outreach agent."""

import logging
import os
from datetime import datetime, timezone

from app.agent.state import AgentState
from app.agent.escalation import get_strategy_for_level, should_mark_cold, get_days_until_next_followup
from app.config import settings
from app.services.llm_service import llm_service
from app.services.gmail_service import gmail_service

logger = logging.getLogger(__name__)


def _load_one_pager() -> str:
    """Load Rajamohan's one-pager from disk."""
    try:
        path = settings.one_pager_path
        if os.path.exists(path):
            with open(path, "r") as f:
                return f.read()
    except Exception as e:
        logger.warning(f"Failed to load one-pager: {e}")
    return "Rajamohan is an experienced technology leader with 20+ years in building scalable platforms, leading engineering teams, and driving digital transformation. He is seeking a CTO role with a 5 Cr+ package."


async def observe_node(state: AgentState) -> dict:
    """
    Node 1: Observe current state.
    Loads context, checks for new inbound messages.
    """
    logger.info(f"[OBSERVE] Contact: {state['contact_name']} at {state['firm_name']}")

    # If we don't have thread history yet, it stays as provided
    # The caller (jobs) is responsible for loading thread history from DB

    return {
        "error": None,
    }


async def reason_node(state: AgentState) -> dict:
    """
    Node 2: Reason about what to do next using LLM.
    """
    logger.info(f"[REASON] Contact: {state['contact_name']} | Status: {state['current_status']} | Level: {state['escalation_level']}")

    # If there's a new inbound message, we need to analyze and respond
    if state.get("new_inbound_message"):
        return {
            "action_decided": "analyze_and_respond",
            "action_reasoning": "New inbound message detected — need to analyze and respond.",
        }

    # If contact is cold or converted, skip
    if state["current_status"] in ("cold", "converted"):
        return {
            "action_decided": "skip",
            "action_reasoning": f"Contact is already {state['current_status']}.",
        }

    # If should be marked cold (exhausted escalation)
    if should_mark_cold(state["escalation_level"]):
        return {
            "action_decided": "mark_cold",
            "action_reasoning": "All escalation levels exhausted with no response.",
        }

    # If new contact, send initial outreach
    if state["current_status"] == "new":
        return {
            "action_decided": "send_initial",
            "action_reasoning": "New contact — sending initial outreach with one-pager.",
        }

    # For contacted status, use LLM to decide
    contact_info = {
        "name": state["contact_name"],
        "title": state["contact_title"],
        "firm_name": state["firm_name"],
        "status": state["current_status"],
        "contact_count": state["escalation_level"],
    }

    decision = await llm_service.decide_next_action(
        contact_info=contact_info,
        thread_history=state.get("thread_history", []),
        escalation_level=state["escalation_level"],
        days_since_last_contact=state.get("days_since_last_contact", 0),
    )

    action = decision.get("action", "wait")
    reasoning = decision.get("reasoning", "LLM decision")

    # Map LLM actions to our action types
    if action in ("send_followup", "send_response"):
        return {
            "action_decided": "send_followup",
            "action_reasoning": reasoning,
            "strategy": decision.get("new_strategy") or get_strategy_for_level(state["escalation_level"]),
        }
    elif action == "change_strategy":
        return {
            "action_decided": "send_followup",
            "action_reasoning": reasoning,
            "strategy": decision.get("new_strategy", "different_angle"),
        }
    elif action == "mark_cold":
        return {
            "action_decided": "mark_cold",
            "action_reasoning": reasoning,
        }
    else:
        return {
            "action_decided": "wait",
            "action_reasoning": reasoning,
        }


async def compose_node(state: AgentState) -> dict:
    """
    Node 3: Compose the email using LLM.
    """
    action = state.get("action_decided")

    if action in ("skip", "wait", "mark_cold"):
        return {"email_composed": None}

    one_pager = _load_one_pager()

    if action == "send_initial":
        logger.info(f"[COMPOSE] Initial email for {state['contact_name']}")
        email = await llm_service.compose_initial_email(
            contact_name=state["contact_name"],
            contact_title=state.get("contact_title", ""),
            firm_name=state["firm_name"],
            one_pager=one_pager,
        )
        return {"email_composed": email}

    elif action == "send_followup":
        logger.info(f"[COMPOSE] Follow-up for {state['contact_name']} (level {state['escalation_level']})")
        email = await llm_service.compose_followup(
            contact_name=state["contact_name"],
            firm_name=state["firm_name"],
            thread_history=state.get("thread_history", []),
            escalation_level=state["escalation_level"],
            strategy=state.get("strategy", "standard"),
        )
        return {"email_composed": email}

    elif action == "analyze_and_respond":
        inbound = state.get("new_inbound_message", {})
        logger.info(f"[COMPOSE] Response to {state['contact_name']}")

        # First analyze the response
        analysis = await llm_service.analyze_response(
            message_body=inbound.get("body_text", ""),
            thread_context=state.get("thread_history", []),
        )

        # Then compose a reply
        email = await llm_service.compose_response(
            contact_name=state["contact_name"],
            firm_name=state["firm_name"],
            thread_history=state.get("thread_history", []),
            inbound_message=inbound.get("body_text", ""),
            analysis=analysis,
        )

        return {
            "email_composed": email,
            "analysis_result": analysis,
        }

    return {"email_composed": None}


async def act_node(state: AgentState) -> dict:
    """
    Node 4: Execute the decided action — send email, update status, etc.
    """
    action = state.get("action_decided")
    email = state.get("email_composed")

    if action in ("skip", "wait") or not email:
        logger.info(f"[ACT] {action} for {state['contact_name']}")
        return {"send_result": None}

    if action == "mark_cold":
        logger.info(f"[ACT] Marking {state['contact_name']} as cold")
        return {"send_result": {"action": "mark_cold"}}

    # Send the email
    logger.info(f"[ACT] Sending email to {state['contact_email']} — subject: {email.get('subject', 'N/A')}")

    try:
        result = await gmail_service.send_email(
            to=state["contact_email"],
            subject=email.get("subject", f"Opportunity — {state['contact_name']}"),
            body_text=email.get("body_text", ""),
            body_html=email.get("body_html"),
            thread_id=state.get("gmail_thread_id"),
        )

        if result:
            logger.info(f"[ACT] Email sent successfully — message_id={result.get('message_id')}")
            return {"send_result": result}
        else:
            logger.error(f"[ACT] Failed to send email to {state['contact_email']}")
            return {"error": "Gmail send failed", "send_result": None}

    except Exception as e:
        logger.error(f"[ACT] Email send error: {e}")
        return {"error": str(e), "send_result": None}
