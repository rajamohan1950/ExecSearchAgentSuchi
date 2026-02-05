"""Escalation policy for outreach follow-ups.

The agent follows this schedule but can override it based on LLM reasoning.
If a contact responds at any level, the escalation resets and the agent
switches to a response-driven conversation mode.
"""

from typing import Optional


# Level → (days to wait before this level, strategy to use)
ESCALATION_SCHEDULE: dict[int, dict] = {
    0: {"days_wait": 0, "strategy": "standard", "label": "Initial outreach"},
    1: {"days_wait": 4, "strategy": "standard", "label": "Soft follow-up"},
    2: {"days_wait": 7, "strategy": "different_angle", "label": "Different angle"},
    3: {"days_wait": 10, "strategy": "urgent", "label": "Urgent / time-sensitive"},
    4: {"days_wait": 14, "strategy": "warm_intro", "label": "Final attempt"},
}

MAX_ESCALATION_LEVEL = 5  # At this level → mark cold


def get_escalation_config(level: int) -> Optional[dict]:
    """Get escalation config for a given level. Returns None if exhausted."""
    if level >= MAX_ESCALATION_LEVEL:
        return None
    return ESCALATION_SCHEDULE.get(level)


def get_days_until_next_followup(current_level: int) -> Optional[int]:
    """How many days to wait before the next follow-up."""
    next_config = get_escalation_config(current_level + 1)
    if not next_config:
        return None
    return next_config["days_wait"]


def get_strategy_for_level(level: int) -> str:
    """Get the recommended strategy for an escalation level."""
    config = get_escalation_config(level)
    return config["strategy"] if config else "standard"


def should_mark_cold(level: int) -> bool:
    """Should this contact be marked as cold?"""
    return level >= MAX_ESCALATION_LEVEL
