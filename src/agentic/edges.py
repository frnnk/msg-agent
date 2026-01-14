"""
Contains functions representing conditional edges, where routing to nodes depends on state.
"""

from langgraph.graph import END
from agentic.state import RequestState


def continue_to_tool(state: RequestState):
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""
    messages = state["messages"]
    last_message = messages[-1]

    if last_message.tool_calls:
        return "use_tools"

    return "response_formatter"

def oauth_url_detection(state: RequestState):
    """Route to response_formatter if URL OAuth is detected, otherwise continue to task executor"""
    if state.get('is_oauth'):
        return "response_formatter"

    return "task_executor"