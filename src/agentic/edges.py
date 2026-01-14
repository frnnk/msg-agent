"""
Contains functions representing conditional edges, where routing to nodes depends on state.
"""

from langgraph.graph import END
from agentic.state import RequestState


def should_continue(state: RequestState):
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""
    messages = state["messages"]
    last_message = messages[-1]

    if last_message.tool_calls:
        return "use_tools"

    return END