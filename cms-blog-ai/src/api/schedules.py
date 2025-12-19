"""
Schedules API endpoints - manage automatic post scheduling.

THIS IS THE KEY API FOR THE AI SCHEDULER FEATURE.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..database import get_db
from ..models.agent import Agent
from ..models.schedule import ScheduleConfig, INTERVAL_CRON_MAP, ScheduleInterval
from ..schemas.schedule import ScheduleCreate, ScheduleUpdate, ScheduleResponse

router = APIRouter(prefix="/schedules", tags=["Schedules"])


@router.post("", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule_data: ScheduleCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new schedule configuration for an agent.

    This enables automatic post generation at the specified interval.
    The scheduler runs via Celery Beat and checks for agents that need
    to generate posts based on their cron expressions.
    """
    # Check agent exists
    result = await db.execute(
        select(Agent).where(Agent.id == schedule_data.agent_id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    # Check if agent already has a schedule
    existing = await db.execute(
        select(ScheduleConfig).where(
            ScheduleConfig.agent_id == schedule_data.agent_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent already has a schedule. Update or delete it first.",
        )

    # Create schedule
    new_schedule = ScheduleConfig(
        agent_id=schedule_data.agent_id,
        interval=schedule_data.interval,
        publish_hour=schedule_data.publish_hour,
        timezone=schedule_data.timezone,
        auto_publish=schedule_data.auto_publish,
        target_keywords=schedule_data.target_keywords,
        exclude_keywords=schedule_data.exclude_keywords,
        post_length=schedule_data.post_length,
    )

    # Also update agent's schedule_cron for the task scheduler
    cron_expression = new_schedule.get_cron_expression()
    agent.schedule_cron = cron_expression

    db.add(new_schedule)
    await db.commit()
    await db.refresh(new_schedule)

    return ScheduleResponse(
        id=new_schedule.id,
        agent_id=new_schedule.agent_id,
        interval=new_schedule.interval,
        interval_display=new_schedule.get_interval_display(),
        publish_hour=new_schedule.publish_hour,
        timezone=new_schedule.timezone,
        is_active=new_schedule.is_active,
        auto_publish=new_schedule.auto_publish,
        target_keywords=new_schedule.target_keywords,
        exclude_keywords=new_schedule.exclude_keywords,
        post_length=new_schedule.post_length,
        cron_expression=new_schedule.get_cron_expression(),
        total_posts_generated=new_schedule.total_posts_generated,
        successful_posts=new_schedule.successful_posts,
        failed_posts=new_schedule.failed_posts,
        last_run_at=new_schedule.last_run_at,
        next_run_at=new_schedule.next_run_at,
        created_at=new_schedule.created_at,
        updated_at=new_schedule.updated_at,
    )


@router.get("")
async def list_schedules(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List all schedule configurations."""
    query = select(ScheduleConfig)

    if is_active is not None:
        query = query.where(ScheduleConfig.is_active == is_active)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    query = query.order_by(ScheduleConfig.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    schedules = result.scalars().all()

    items = []
    for s in schedules:
        items.append(ScheduleResponse(
            id=s.id,
            agent_id=s.agent_id,
            interval=s.interval,
            interval_display=s.get_interval_display(),
            publish_hour=s.publish_hour,
            timezone=s.timezone,
            is_active=s.is_active,
            auto_publish=s.auto_publish,
            target_keywords=s.target_keywords,
            exclude_keywords=s.exclude_keywords,
            post_length=s.post_length,
            cron_expression=s.get_cron_expression(),
            total_posts_generated=s.total_posts_generated,
            successful_posts=s.successful_posts,
            failed_posts=s.failed_posts,
            last_run_at=s.last_run_at,
            next_run_at=s.next_run_at,
            created_at=s.created_at,
            updated_at=s.updated_at,
        ))

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get schedule configuration by ID."""
    result = await db.execute(
        select(ScheduleConfig).where(ScheduleConfig.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found",
        )

    return ScheduleResponse(
        id=schedule.id,
        agent_id=schedule.agent_id,
        interval=schedule.interval,
        interval_display=schedule.get_interval_display(),
        publish_hour=schedule.publish_hour,
        timezone=schedule.timezone,
        is_active=schedule.is_active,
        auto_publish=schedule.auto_publish,
        target_keywords=schedule.target_keywords,
        exclude_keywords=schedule.exclude_keywords,
        post_length=schedule.post_length,
        cron_expression=schedule.get_cron_expression(),
        total_posts_generated=schedule.total_posts_generated,
        successful_posts=schedule.successful_posts,
        failed_posts=schedule.failed_posts,
        last_run_at=schedule.last_run_at,
        next_run_at=schedule.next_run_at,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
    )


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: UUID,
    schedule_data: ScheduleUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update schedule configuration."""
    result = await db.execute(
        select(ScheduleConfig).where(ScheduleConfig.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found",
        )

    update_data = schedule_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(schedule, field, value)

    # Update agent's cron expression if interval or hour changed
    if 'interval' in update_data or 'publish_hour' in update_data:
        agent_result = await db.execute(
            select(Agent).where(Agent.id == schedule.agent_id)
        )
        agent = agent_result.scalar_one_or_none()
        if agent:
            agent.schedule_cron = schedule.get_cron_expression()

    await db.commit()
    await db.refresh(schedule)

    return ScheduleResponse(
        id=schedule.id,
        agent_id=schedule.agent_id,
        interval=schedule.interval,
        interval_display=schedule.get_interval_display(),
        publish_hour=schedule.publish_hour,
        timezone=schedule.timezone,
        is_active=schedule.is_active,
        auto_publish=schedule.auto_publish,
        target_keywords=schedule.target_keywords,
        exclude_keywords=schedule.exclude_keywords,
        post_length=schedule.post_length,
        cron_expression=schedule.get_cron_expression(),
        total_posts_generated=schedule.total_posts_generated,
        successful_posts=schedule.successful_posts,
        failed_posts=schedule.failed_posts,
        last_run_at=schedule.last_run_at,
        next_run_at=schedule.next_run_at,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
    )


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete schedule configuration."""
    result = await db.execute(
        select(ScheduleConfig).where(ScheduleConfig.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found",
        )

    # Clear agent's cron expression
    agent_result = await db.execute(
        select(Agent).where(Agent.id == schedule.agent_id)
    )
    agent = agent_result.scalar_one_or_none()
    if agent:
        agent.schedule_cron = None

    await db.delete(schedule)
    await db.commit()


@router.post("/{schedule_id}/activate")
async def activate_schedule(
    schedule_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Activate a schedule."""
    result = await db.execute(
        select(ScheduleConfig).where(ScheduleConfig.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found",
        )

    schedule.is_active = True

    # Update agent's cron
    agent_result = await db.execute(
        select(Agent).where(Agent.id == schedule.agent_id)
    )
    agent = agent_result.scalar_one_or_none()
    if agent:
        agent.schedule_cron = schedule.get_cron_expression()

    await db.commit()

    return {"message": "Schedule activated", "schedule_id": str(schedule_id)}


@router.post("/{schedule_id}/deactivate")
async def deactivate_schedule(
    schedule_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a schedule."""
    result = await db.execute(
        select(ScheduleConfig).where(ScheduleConfig.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found",
        )

    schedule.is_active = False

    # Clear agent's cron
    agent_result = await db.execute(
        select(Agent).where(Agent.id == schedule.agent_id)
    )
    agent = agent_result.scalar_one_or_none()
    if agent:
        agent.schedule_cron = None

    await db.commit()

    return {"message": "Schedule deactivated", "schedule_id": str(schedule_id)}
