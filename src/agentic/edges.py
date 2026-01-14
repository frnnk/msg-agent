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

    return END

def oauth_url_detection(state: RequestState):
    """Route to END if URL OAuth is detected, otherwise continue to task executor"""
    if state["pending_action"] is not None and state['pending_action']["kind"] == "mcp_elicitation":
        return END

    return "task_executor"