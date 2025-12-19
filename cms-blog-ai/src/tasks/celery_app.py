"""
Celery application configuration.
Handles asynchronous task execution and scheduled jobs.

IMPORTANT: This is the core of the AI scheduler functionality.

Usage:
    1. Start Redis (broker)
    2. Start Celery worker: celery -A src.tasks.celery_app worker -l info
    3. Start Celery beat (scheduler): celery -A src.tasks.celery_app beat -l info

For production, run worker and beat separately:
    celery -A src.tasks.celery_app worker -l info -Q generation
    celery -A src.tasks.celery_app beat -l info
"""

from celery import Celery
from celery.schedules import crontab
from ..config import settings

# Create Celery application
celery_app = Celery(
    "cms_blog_ai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "src.tasks.post_tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task execution
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max task time
    task_soft_time_limit=3000,  # 50 min soft limit

    # Results
    result_expires=86400,  # Results expire after 24 hours
    result_extended=True,

    # Retries
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Worker
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,

    # Beat schedule (cron jobs) - THE SCHEDULER
    beat_schedule={
        # Process pending agent generations based on cron schedules
        # This is the main scheduler task - runs every 5 minutes
        "process-agent-schedules": {
            "task": "src.tasks.post_tasks.process_agent_schedules",
            "schedule": crontab(minute=f"*/{settings.SCHEDULER_CHECK_INTERVAL_MINUTES}"),
        },
        # Publish scheduled posts
        "publish-scheduled-posts": {
            "task": "src.tasks.post_tasks.publish_scheduled_posts",
            "schedule": crontab(minute="*/1"),  # Every minute
        },
    },
)

# Task routes (for queue-based routing)
celery_app.conf.task_routes = {
    "src.tasks.post_tasks.*": {"queue": "generation"},
}
