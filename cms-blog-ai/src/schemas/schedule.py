"""
Pydantic schemas for schedule configurations.
"""

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List


class ScheduleCreate(BaseModel):
    """Create schedule configuration."""
    agent_id: UUID
    interval: str = Field("weekly", pattern="^(daily|every_3_days|weekly|biweekly)$")
    publish_hour: int = Field(10, ge=0, le=23)
    timezone: str = Field("UTC", max_length=50)
    auto_publish: bool = True
    target_keywords: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None
    post_length: str = Field("long", pattern="^(short|medium|long|very_long)$")


class ScheduleUpdate(BaseModel):
    """Update schedule configuration."""
    interval: Optional[str] = Field(None, pattern="^(daily|every_3_days|weekly|biweekly)$")
    publish_hour: Optional[int] = Field(None, ge=0, le=23)
    timezone: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    auto_publish: Optional[bool] = None
    target_keywords: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None
    post_length: Optional[str] = Field(None, pattern="^(short|medium|long|very_long)$")


class ScheduleResponse(BaseModel):
    """Schedule configuration response."""
    id: UUID
    agent_id: UUID
    interval: str
    interval_display: str
    publish_hour: int
    timezone: str
    is_active: bool
    auto_publish: bool
    target_keywords: Optional[List[str]]
    exclude_keywords: Optional[List[str]]
    post_length: str
    cron_expression: str
    total_posts_generated: int
    successful_posts: int
    failed_posts: int
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
