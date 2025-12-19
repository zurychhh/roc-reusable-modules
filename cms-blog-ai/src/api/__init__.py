"""
CMS Blog AI - API Endpoints
FastAPI routers for posts, agents, and schedules.
"""

from .posts import router as posts_router
from .agents import router as agents_router
from .schedules import router as schedules_router

__all__ = [
    "posts_router",
    "agents_router",
    "schedules_router",
]
