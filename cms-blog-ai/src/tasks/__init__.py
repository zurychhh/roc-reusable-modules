"""
CMS Blog AI - Celery Tasks
Background tasks for scheduled post generation.
"""

from .post_tasks import (
    generate_post_for_agent,
    process_agent_schedules,
)
from .celery_app import celery_app

__all__ = [
    "celery_app",
    "generate_post_for_agent",
    "process_agent_schedules",
]
