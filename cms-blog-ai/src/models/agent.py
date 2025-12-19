"""
Agent Model - AI content generation expert.
"""

import uuid
from datetime import datetime
from sqlalchemy import Boolean, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ..database import Base


class Agent(Base):
    """
    AI Agent - expert for specific domain with persona and settings.

    An agent represents a content creator persona with:
    - Expertise area (e.g., "law", "marketing", "tech")
    - Writing tone and style
    - Post length preferences
    - Scheduling configuration
    """

    __tablename__ = "agents"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    expertise: Mapped[str] = mapped_column(String(100), nullable=False)

    # AI Persona configuration
    persona: Mapped[str | None] = mapped_column(Text, nullable=True)
    tone: Mapped[str] = mapped_column(String(50), default="professional")
    post_length: Mapped[str] = mapped_column(String(50), default="medium")

    # Scheduling
    schedule_cron: Mapped[str | None] = mapped_column(String(100), nullable=True)
    workflow: Mapped[str] = mapped_column(String(50), default="draft")

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Additional settings (JSON storage)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    posts = relationship("Post", back_populates="agent", cascade="all, delete-orphan")
    schedule_configs = relationship("ScheduleConfig", back_populates="agent", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Agent {self.name} - {self.expertise}>"

    def get_word_count_target(self) -> int:
        """Get target word count based on post_length setting."""
        targets = {
            "short": 500,
            "medium": 1000,
            "long": 2000,
            "very_long": 3000
        }
        return targets.get(self.post_length, 1000)

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "name": self.name,
            "expertise": self.expertise,
            "persona": self.persona,
            "tone": self.tone,
            "post_length": self.post_length,
            "schedule_cron": self.schedule_cron,
            "workflow": self.workflow,
            "is_active": self.is_active,
            "settings": self.settings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
