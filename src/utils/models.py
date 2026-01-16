"""
Provides FastAPI Pydantic models for various API endpoints.
"""

from typing import List, Optional
from pydantic import BaseModel


class RunBody(BaseModel):
    """Request body for initiating a new user request"""
    thread_id: str
    user_request: str


class ToolApproval(BaseModel):
    """User's approval decision for a single tool call"""
    call_id: str
    approved: bool
    feedback: Optional[str] = None


class ResumeBody(BaseModel):
    """Request body for resuming after human confirmation interrupt"""
    thread_id: str
    approvals: List[ToolApproval]
