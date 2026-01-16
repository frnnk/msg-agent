"""
Implementation of state shared across LangGraph nodes of the message assistant agentic system.
"""

from typing import TypedDict, Literal, NotRequired, List, Any
from langgraph.graph import MessagesState


NO_ACTION = {
    'kind': 'no_action_needed'
}

class ToolCallInfo(TypedDict):
    """Represents a single tool call needing confirmation."""
    call_id: str
    tool_name: str
    arguments: dict[str, Any]


class RejectedToolFeedback(TypedDict):
    """Feedback for a rejected tool call."""
    call_id: str
    tool_name: str
    feedback: str


class ApprovalOutcome(TypedDict):
    """Outcome after processing user approvals."""
    all_approved: bool
    approved_call_ids: List[str]
    rejected_feedback: List[RejectedToolFeedback]


class PendingApproval(TypedDict):
    kind: Literal["confirmation"]
    tool_calls: List[ToolCallInfo]


class PendingMCPElicitation(TypedDict):
    kind: Literal["oauth_url", "form_elicitation"]
    elicitation_id: str
    url: NotRequired[str] # for oauth_url kind
    schema: NotRequired[dict]  # JSON schema for form_elicitation kind
    message: NotRequired[str]


PendingAction = PendingApproval | PendingMCPElicitation


class RequestState(MessagesState):
    allowed_tool_types: list[str]
    pending_action: NotRequired[PendingAction]
    final_response: NotRequired[str]
    approval_outcome: NotRequired[ApprovalOutcome]

