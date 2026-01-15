"""
Contains functions representing conditional edges, where routing to nodes depends on state.
"""

import logging
from langgraph.graph import END
from agentic.state import RequestState, NO_ACTION


def continue_to_tool(state: RequestState):
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""
    messages = state["messages"]
    last_message = messages[-1]

    if last_message.tool_calls:
        logging.info(f"Routing from Task Executor to use_tools")
        return "use_tools"

    logging.info(f"Routing from Task Executor to response_formatter")
    return "response_formatter"

def oauth_url_detection(state: RequestState):
    """Route to response_formatter if URL OAuth is detected, otherwise continue to task executor"""
    if state.get('pending_action', NO_ACTION)['kind'] == 'oauth_url':
        logging.info(f"Routing from Tool Node to response_formatter")
        return "response_formatter"

    logging.info(f"Routing from Tool node back to Task Executor")
    return "task_executor"