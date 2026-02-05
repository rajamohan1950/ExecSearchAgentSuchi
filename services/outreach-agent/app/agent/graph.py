"""LangGraph state machine for the autonomous outreach agent.

Flow:
    observe → reason → compose → act → END

The graph processes one contact at a time. The scheduler triggers
graph execution for each contact that needs attention.
"""

import logging

from langgraph.graph import StateGraph, END

from app.agent.state import AgentState
from app.agent.nodes import observe_node, reason_node, compose_node, act_node

logger = logging.getLogger(__name__)


def build_agent_graph() -> StateGraph:
    """Build and compile the agent LangGraph."""

    workflow = StateGraph(AgentState)

    # Define nodes
    workflow.add_node("observe", observe_node)
    workflow.add_node("reason", reason_node)
    workflow.add_node("compose", compose_node)
    workflow.add_node("act", act_node)

    # Define edges — linear flow
    workflow.add_edge("observe", "reason")
    workflow.add_edge("reason", "compose")
    workflow.add_edge("compose", "act")
    workflow.add_edge("act", END)

    # Entry point
    workflow.set_entry_point("observe")

    return workflow.compile()


# Compiled graph — reuse across invocations
agent_graph = build_agent_graph()
