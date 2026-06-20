"""
Structured models for how agents should respond.
"""

from pydantic import BaseModel, Field
from typing import List, Literal


class PolicyRouterOut(BaseModel):
    decision: str
    note: str
    # TODO(template): list your tool types here to match TOOL_MAPPING keys
    allowed_tool_types: List[Literal['example']]