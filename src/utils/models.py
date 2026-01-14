"""
Provides FastAPI Pydantic models for various API endpoints.
"""

from pydantic import BaseModel


class RunBody(BaseModel):
    thread_id: str
    user_request: str
