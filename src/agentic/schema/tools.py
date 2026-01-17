"""
Provides LangChain tools for the agentic system.
"""

from langchain_core.tools import tool

CLARIFICATION_TOOL_NAME = "request_clarification"


@tool
def request_clarification(question: str, context: str = "") -> str:
    """Request clarification from the user when information is ambiguous."""
    return "Clarification pending"
