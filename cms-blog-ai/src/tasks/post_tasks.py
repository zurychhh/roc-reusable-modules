"""
Post generation tasks.

THE CORE SCHEDULER FUNCTIONALITY:
- generate_post_for_agent: Generates a single post for an agent
- process_agent_schedules: Checks cron schedules and triggers generation
- publish_scheduled_posts: Publishes posts at their scheduled time

This is the most important file for the AI scheduler feature.
"""

import logging
from typing import Optional
from datetime import datetime
from uuid import UUID

from celery import Task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from croniter import croniter

from .celery_app import celery_app
from ..database import AsyncSessionLocal
from ..models.agent import Agent
from ..models.post import Post
from ..models.schedule import ScheduleConfig
from ..ai.post_generator import get_post_generator
from ..services.seo_service import SEOService

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task with database session management."""

    _db: Optional[AsyncSession] = None

    async def get_db(self) -> AsyncSession:
        """Get async database session."""
        if self._db is None:
            self._db = AsyncSessionLocal()
        return self._db

    async def close_db(self):
        """Close database session."""
        if self._db:
            await self._db.close()
            self._db = None


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="src.tasks.post_tasks.generate_post_for_agent",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    max_retries=3,
)
def generate_post_for_agent(
    self,
    agent_id: str,
    topic: Optional[str] = None,
    keyword: Optional[str] = None
):
    """
    Generate a blog post for a specific agent.

    This task is triggered either:
    1. Manually via API
    2. Automatically by process_agent_schedules based on cron

    Args:
        agent_id: Agent UUID string
        topic: Optional topic override
        keyword: Optional keyword override

    Returns:
        dict with post_id and status
    """
    import asyncio

    async def _generate():
        db = await self.get_db()
        try:
            # Get agent
            result = await db.execute(
                select(Agent).where(Agent.id == UUID(agent_id))
            )
            agent = result.scalar_one_or_none()

            if not agent or not agent.is_active:
                logger.warning(f"Agent {agent_id} not found or inactive")
                return {"success": False, "error": "Agent not found or inactive"}

            # Generate post
            post_generator = get_post_generator()
            seo_service = SEOService()

            # Use provided topic/keyword or agent's expertise as fallback
            post_topic = topic or f"Latest trends in {agent.expertise or 'technology'}"
            post_keyword = keyword or (agent.expertise or "technology")

            generation_result = await post_generator.generate_post(
                agent=agent,
                topic=post_topic,
                keyword=post_keyword,
            )

            # Calculate SEO metrics
            readability_score = seo_service.calculate_readability_score(
                generation_result["content"]
            )

            keyword_density = {}
            if generation_result["keywords"]:
                keyword_density = seo_service.calculate_keyword_density(
                    generation_result["content"],
                    generation_result["keywords"]
                )

            # Generate slug
            slug = seo_service.generate_slug(generation_result["title"])

            # Create post
            new_post = Post(
                agent_id=agent.id,
                title=generation_result["title"],
                content=generation_result["content"],
                meta_title=generation_result["meta_title"],
                meta_description=generation_result["meta_description"],
                keywords=generation_result["keywords"],
                slug=slug,
                status="draft",
                tokens_used=generation_result["tokens_used"],
                word_count=generation_result["word_count"],
                readability_score=readability_score,
                keyword_density=keyword_density,
            )

            db.add(new_post)
            await db.commit()
            await db.refresh(new_post)

            # Update schedule stats if this was a scheduled run
            schedule_result = await db.execute(
                select(ScheduleConfig).where(
                    ScheduleConfig.agent_id == agent.id,
                    ScheduleConfig.is_active == True
                )
            )
            schedule = schedule_result.scalar_one_or_none()
            if schedule:
                schedule.total_posts_generated += 1
                schedule.successful_posts += 1
                schedule.last_run_at = datetime.utcnow()
                await db.commit()

            logger.info(f"Generated post {new_post.id} for agent {agent_id}")

            return {
                "success": True,
                "post_id": str(new_post.id),
                "title": new_post.title,
                "word_count": new_post.word_count,
                "status": new_post.status,
            }

        except Exception as e:
            await db.rollback()

            # Update schedule failure stats
            try:
                schedule_result = await db.execute(
                    select(ScheduleConfig).where(
                        ScheduleConfig.agent_id == UUID(agent_id),
                        ScheduleConfig.is_active == True
                    )
                )
                schedule = schedule_result.scalar_one_or_none()
                if schedule:
                    schedule.failed_posts += 1
                    await db.commit()
            except Exception:
                pass

            logger.error(f"Error generating post for agent {agent_id}: {e}", exc_info=True)
            raise
        finally:
            await self.close_db()

    return asyncio.run(_generate())


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="src.tasks.post_tasks.process_agent_schedules",
)
def process_agent_schedules(self):
    """
    Process all agents with cron schedules.

    THIS IS THE MAIN SCHEDULER TASK.

    Checks which agents should generate posts now based on their schedule_cron.
    Called every 5 minutes by Celery Beat (configurable).

    The scheduler logic:
    1. Find all active agents with a schedule_cron set
    2. For each agent, check if the cron should have run in the last check interval
    3. If yes, trigger post generation

    Returns:
        dict with number of agents processed and posts triggered
    """
    import asyncio

    async def _process():
        db = await self.get_db()
        try:
            # Get all active agents with schedules
            result = await db.execute(
                select(Agent).where(
                    Agent.is_active == True,
                    Agent.schedule_cron.is_not(None)
                )
            )
            agents = result.scalars().all()

            now = datetime.utcnow()
            posts_triggered = 0

            for agent in agents:
                try:
                    # Check if agent should run now
                    cron = croniter(agent.schedule_cron, now)
                    prev_run = cron.get_prev(datetime)

                    # Check if it should have run in last 5 minutes (or configured interval)
                    from ..config import settings
                    interval_seconds = settings.SCHEDULER_CHECK_INTERVAL_MINUTES * 60

                    if (now - prev_run).total_seconds() < interval_seconds:
                        # Trigger post generation asynchronously
                        generate_post_for_agent.delay(str(agent.id))
                        posts_triggered += 1
                        logger.info(f"Triggered post generation for agent {agent.id} ({agent.name})")

                except Exception as e:
                    logger.error(f"Error processing schedule for agent {agent.id}: {e}")
                    continue

            logger.info(f"Processed {len(agents)} agents, triggered {posts_triggered} post generations")

            return {
                "success": True,
                "agents_checked": len(agents),
                "posts_triggered": posts_triggered,
            }

        except Exception as e:
            logger.error(f"Error processing agent schedules: {e}", exc_info=True)
            raise
        finally:
            await self.close_db()

    return asyncio.run(_process())


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="src.tasks.post_tasks.publish_scheduled_posts",
)
def publish_scheduled_posts(self):
    """
    Publish posts that are scheduled for now.

    Checks for posts with status='scheduled' and scheduled_at <= now,
    then updates their status to 'published'.

    Returns:
        dict with number of posts published
    """
    import asyncio

    async def _publish():
        db = await self.get_db()
        try:
            now = datetime.utcnow()

            # Get scheduled posts ready for publishing
            result = await db.execute(
                select(Post).where(
                    Post.status == "scheduled",
                    Post.scheduled_at <= now
                )
            )
            posts = result.scalars().all()

            published_count = 0

            for post in posts:
                try:
                    post.status = "published"
                    post.published_at = now
                    published_count += 1
                    logger.info(f"Published post {post.id}: {post.title}")
                except Exception as e:
                    logger.error(f"Error publishing post {post.id}: {e}")
                    continue

            await db.commit()

            logger.info(f"Published {published_count} scheduled posts")

            return {
                "success": True,
                "posts_published": published_count,
            }

        except Exception as e:
            await db.rollback()
            logger.error(f"Error publishing scheduled posts: {e}", exc_info=True)
            raise
        finally:
            await self.close_db()

    return asyncio.run(_publish())
