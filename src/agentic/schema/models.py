"""
Models for how agents should respond.
"""

from pydantic import BaseModel, Field
from typing import List


class PolicyRouterOut(BaseModel):
    decision: str
    note: str
    allowed_tool_types: List[str]