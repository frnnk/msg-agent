"""
Implementation of state shared across LangGraph nodes of the message assistant agentic system.
"""

from typing import TypedDict, Literal, NotRequired
from langgraph.graph import MessagesState


class PendingApproval(TypedDict):
    kind: Literal["confirmation"]
    tool_name: str
    tool_args: dict
    rationale: str

class PendingMCPElicitation(TypedDict):
    kind: Literal["oauth_url", "form_elicitation"]
    elicitation_id: str
    url: NotRequired[str] # for oauth_url kind
    schema: NotRequired[dict]  # JSON schema for form_elicitation kind
    message: NotRequired[str]

NO_ACTION = {
    'kind': 'no_action_needed'
}

PendingAction = PendingApproval | PendingMCPElicitation

class RequestState(MessagesState):
    allowed_tool_types: list[str]
    pending_action: NotRequired[PendingAction]
    final_response: NotRequired[str]

