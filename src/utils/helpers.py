"""
Provides shared helper functions.
"""

from langchain_core.messages import AIMessage


def get_last_ai_message(state):
    """Get the most recent AIMessage from state messages."""
    for message in reversed(state['messages']):
        if isinstance(message, AIMessage):
            return message
    return None


def tool_catalog(tools):
    return [
        {
            "name": t.name,
            "description": (t.description or "").strip()[:400],
        }
        for t in tools
    ]