"""
Pydantic schemas for blog posts.
"""

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any, List


class PostCreate(BaseModel):
    """Create post schema - for manual post creation."""
    agent_id: UUID
    title: str = Field(..., min_length=1, max_length=500)
    slug: Optional[str] = None
    content: str = Field(..., min_length=1)
    excerpt: Optional[str] = None
    meta_title: Optional[str] = Field(None, max_length=70)
    meta_description: Optional[str] = Field(None, max_length=160)
    keywords: Optional[List[str]] = None
    status: str = Field("draft", pattern="^(draft|scheduled|published)$")


class PostUpdate(BaseModel):
    """Update post schema."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    slug: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    meta_title: Optional[str] = Field(None, max_length=70)
    meta_description: Optional[str] = Field(None, max_length=160)
    keywords: Optional[List[str]] = None
    schema_markup: Optional[Dict[str, Any]] = None
    og_image_url: Optional[str] = None
    canonical_url: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(draft|scheduled|published|failed)$")


class PostGenerateRequest(BaseModel):
    """AI post generation request."""
    agent_id: UUID
    topic: Optional[str] = None
    target_keyword: Optional[str] = None


class PostScheduleRequest(BaseModel):
    """Schedule post for publication."""
    scheduled_at: datetime


class PostResponse(BaseModel):
    """Post response schema."""
    id: UUID
    agent_id: UUID

    # Content
    title: str
    slug: Optional[str]
    content: str
    excerpt: Optional[str]

    # SEO
    meta_title: Optional[str]
    meta_description: Optional[str]
    keywords: List[str]
    schema_markup: Optional[Dict[str, Any]]
    og_image_url: Optional[str]
    canonical_url: Optional[str]

    # Stats
    readability_score: Optional[float]
    keyword_density: Optional[Dict[str, float]]
    word_count: Optional[int]

    # Workflow
    status: str
    scheduled_at: Optional[datetime]
    published_at: Optional[datetime]
    published_url: Optional[str]

    # AI metadata
    source_urls: List[str]
    tokens_used: int

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PostListResponse(BaseModel):
    """Paginated post list response."""
    items: List[PostResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
