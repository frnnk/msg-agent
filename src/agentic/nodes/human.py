"""
Implementation of several HITL nodes within the message assistant agentic system, handling 
confirmations, form elicitations, and url oauth elicitations.
"""

from agentic.state import RequestState
from langchain_core.messages import AIMessage


def get_last_ai_message(state: RequestState):
    for message in reversed(state.messages):
        if isinstance(message, AIMessage):
            return message

async def human_confirmation(state: RequestState):
    last_ai_message = get_last_ai_message(state=state)
    if last_ai_message is None:
        raise ValueError("missing last ai message")

    # for now before we have checkpoint working, just stop and raise an error to stop
    pass

async def human_inquiry(state: RequestState):
    pass