"""
Schedule Model - Automatic post scheduling configuration.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlalchemy import Boolean, String, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ..database import Base


class ScheduleInterval(str, Enum):
    """Available scheduling intervals."""
    DAILY = "daily"
    EVERY_3_DAYS = "every_3_days"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"


# Mapping intervals to cron expressions
INTERVAL_CRON_MAP = {
    ScheduleInterval.DAILY: "0 {hour} * * *",
    ScheduleInterval.EVERY_3_DAYS: "0 {hour} */3 * *",
    ScheduleInterval.WEEKLY: "0 {hour} * * 1",
    ScheduleInterval.BIWEEKLY: "0 {hour} 1,15 * *",
}


class ScheduleConfig(Base):
    """
    Automatic post scheduling configuration.

    Allows configuring:
    - Generation interval (daily, weekly, etc.)
    - Publication time (hour in UTC)
    - Auto-publish or save as draft
    - Target keywords for generation
    - Post length preferences
    """

    __tablename__ = "schedule_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Link to agent
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Schedule configuration
    interval: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=ScheduleInterval.WEEKLY.value
    )

    # Hour of publication (0-23, UTC)
    publish_hour: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10
    )

    # Timezone for display
    timezone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="UTC"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Tracking
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Auto-publish settings
    auto_publish: Mapped[bool] = mapped_column(Boolean, default=True)

    # Content preferences
    target_keywords: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        nullable=True,
        default=list
    )

    exclude_keywords: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        nullable=True,
        default=list
    )

    post_length: Mapped[str] = mapped_column(String(50), default="long")

    # Statistics
    total_posts_generated: Mapped[int] = mapped_column(Integer, default=0)
    successful_posts: Mapped[int] = mapped_column(Integer, default=0)
    failed_posts: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    agent = relationship("Agent", back_populates="schedule_configs")

    def __repr__(self):
        return f"<ScheduleConfig {self.id} - {self.interval}>"

    def get_cron_expression(self) -> str:
        """Generate cron expression based on interval and publish hour."""
        template = INTERVAL_CRON_MAP.get(
            ScheduleInterval(self.interval),
            INTERVAL_CRON_MAP[ScheduleInterval.WEEKLY]
        )
        return template.format(hour=self.publish_hour)

    def get_interval_display(self) -> str:
        """Human-readable interval description."""
        displays = {
            ScheduleInterval.DAILY.value: "Daily",
            ScheduleInterval.EVERY_3_DAYS.value: "Every 3 days",
            ScheduleInterval.WEEKLY.value: "Weekly",
            ScheduleInterval.BIWEEKLY.value: "Biweekly",
        }
        return displays.get(self.interval, self.interval)

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "agent_id": str(self.agent_id),
            "interval": self.interval,
            "interval_display": self.get_interval_display(),
            "publish_hour": self.publish_hour,
            "timezone": self.timezone,
            "is_active": self.is_active,
            "auto_publish": self.auto_publish,
            "target_keywords": self.target_keywords,
            "post_length": self.post_length,
            "cron_expression": self.get_cron_expression(),
            "total_posts_generated": self.total_posts_generated,
            "successful_posts": self.successful_posts,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
        }
