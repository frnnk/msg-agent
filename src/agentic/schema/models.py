"""
Structured models for how agents should respond.
"""

from pydantic import BaseModel, Field
from typing import List, Literal
from mcp_module.adapter import TOOL_MAPPING


class PolicyRouterOut(BaseModel):
    decision: str
    note: str
    allowed_tool_types: List[Literal['calendar']]