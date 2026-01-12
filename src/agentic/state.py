"""
Implementation of state shared across LangGraph nodes of the message assistant agentic system.
"""

from typing import TypedDict, Literal, NotRequired
from langgraph.graph import MessagesState


class PendingApproval(TypedDict):
    kind: Literal["hitl"]
    tool_name: str
    tool_args: dict
    rationale: str

class PendingMCPElicitation(TypedDict):
    kind: Literal["mcp_elicitation"]
    server_name: str
    mode: Literal["url", "form"]
    elicitation_id: str
    url: NotRequired[str] # for url oauth mode
    schema: NotRequired[dict]  # JSON schema for form mode
    message: NotRequired[str]

PendingAction = PendingApproval | PendingMCPElicitation | None

class RequestState(MessagesState):
    pending_action: PendingAction
    allowed_tool_names: list[str]

