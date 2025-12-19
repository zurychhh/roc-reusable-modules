"""
CMS Blog AI - Pydantic Schemas
Request/Response schemas for API endpoints.
"""

from .post import (
    PostCreate,
    PostUpdate,
    PostGenerateRequest,
    PostScheduleRequest,
    PostResponse,
    PostListResponse,
)
from .agent import (
    AgentCreate,
    AgentUpdate,
    AgentResponse,
)
from .schedule import (
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleResponse,
)

__all__ = [
    "PostCreate",
    "PostUpdate",
    "PostGenerateRequest",
    "PostScheduleRequest",
    "PostResponse",
    "PostListResponse",
    "AgentCreate",
    "AgentUpdate",
    "AgentResponse",
    "ScheduleCreate",
    "ScheduleUpdate",
    "ScheduleResponse",
]
