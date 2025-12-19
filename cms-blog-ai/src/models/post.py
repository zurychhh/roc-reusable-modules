"""
Post Model - Blog posts with SEO metadata.
"""

import uuid
from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ..database import Base


class Post(Base):
    """
    Blog post with full SEO metadata.

    Features:
    - Content storage (markdown/HTML)
    - SEO metadata (title, description, keywords)
    - Schema.org markup
    - Readability and keyword density metrics
    - Publishing workflow (draft, scheduled, published)
    - AI generation tracking (tokens, prompts)
    """

    __tablename__ = "posts"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Foreign keys
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Content
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)

    # SEO Metadata
    meta_title: Mapped[str | None] = mapped_column(String(70), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(String(160), nullable=True)
    keywords: Mapped[list] = mapped_column(JSONB, default=list)
    schema_markup: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    og_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    canonical_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # SEO Stats
    readability_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    keyword_density: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Workflow
    status: Mapped[str] = mapped_column(
        String(50),
        default="draft",
        index=True
    )  # draft, scheduled, published, failed
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    published_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # AI Metadata
    source_urls: Mapped[list] = mapped_column(JSONB, default=list)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    generation_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    agent = relationship("Agent", back_populates="posts")

    def __repr__(self):
        return f"<Post {self.title[:50]} ({self.status})>"

    def is_published(self) -> bool:
        """Check if post is published."""
        return self.status == "published"

    def is_draft(self) -> bool:
        """Check if post is draft."""
        return self.status == "draft"

    def is_scheduled(self) -> bool:
        """Check if post is scheduled."""
        return self.status == "scheduled"

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "agent_id": str(self.agent_id),
            "title": self.title,
            "slug": self.slug,
            "content": self.content,
            "excerpt": self.excerpt,
            "meta_title": self.meta_title,
            "meta_description": self.meta_description,
            "keywords": self.keywords,
            "status": self.status,
            "word_count": self.word_count,
            "tokens_used": self.tokens_used,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
        }
