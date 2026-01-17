"""
Contains functions representing conditional edges, where routing to nodes depends on state.
"""

import logging
from langgraph.graph import END
from agentic.state import RequestState, NO_ACTION


def route_from_task_executor(state: RequestState):
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""
    messages = state["messages"]
    last_message = messages[-1]
    pending_kind = state.get('pending_action', NO_ACTION)['kind']

    if pending_kind == 'clarification':
        logging.info("Routing from Task Executor to human_clarification")
        return "human_clarification"

    if pending_kind == 'confirmation':
        return "human_confirmation"

    if last_message.tool_calls:
        logging.info("Routing from Task Executor to use_tools")
        return "use_tools"

    logging.info("Routing from Task Executor to END")
    return END


def oauth_url_detection(state: RequestState):
    """Route to oauth_needed if URL OAuth is detected, otherwise continue to task executor"""
    if state.get('pending_action', NO_ACTION)['kind'] == 'oauth_url':
        logging.info(f"Routing from Tool Node to oauth_needed")
        return "oauth_needed"

    logging.info(f"Routing from Tool node back to Task Executor")
    return "task_executor"


def route_from_human_confirmation(state: RequestState):
    """
    Route based on approval outcome:
    - If any tools were approved -> use_tools (execute approved tools)
    - If all rejected -> task_executor (to handle feedback)
    """
    outcome = state.get('approval_outcome')

    if outcome is None:
        # fallback, shouldn't happen
        logging.warning("No approval_outcome in state, routing to task_executor")
        return "task_executor"

    if outcome['approved_call_ids']:
        logging.info(f"Routing from human_confirmation to use_tools (approved: {len(outcome['approved_call_ids'])} tools)")
        return "use_tools"

    logging.info("Routing from human_confirmation to task_executor (all rejected)")
    return "task_executor"


def route_from_human_clarification(state: RequestState):
    """
    Route based on post-clarification state:
    - If HITL tools pending -> human_confirmation
    - If remaining tools exist -> use_tools
    - Otherwise -> task_executor
    """
    pending_kind = state.get('pending_action', NO_ACTION)['kind']

    if pending_kind == 'confirmation':
        logging.info("Routing from human_clarification to human_confirmation")
        return "human_confirmation"

    messages = state.get('messages', [])
    if messages and hasattr(messages[-1], 'tool_calls') and messages[-1].tool_calls:
        logging.info("Routing from human_clarification to use_tools")
        return "use_tools"

    logging.info("Routing from human_clarification to task_executor")
    return "task_executor"