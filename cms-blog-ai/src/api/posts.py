"""
Posts API endpoints - manage blog posts with SEO metadata.

Provides:
- Manual post creation
- AI post generation
- Post listing and management
- Scheduling for publication
"""

from typing import Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..database import get_db
from ..models.post import Post
from ..models.agent import Agent
from ..schemas.post import (
    PostCreate,
    PostUpdate,
    PostResponse,
    PostListResponse,
    PostGenerateRequest,
    PostScheduleRequest,
)
from ..ai.post_generator import get_post_generator
from ..services.seo_service import SEOService

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: PostCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new post manually (without AI generation).
    Use this for manually written content.
    """
    # Check agent exists
    result = await db.execute(
        select(Agent).where(Agent.id == post_data.agent_id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    # Generate slug if not provided
    seo_service = SEOService()
    slug = post_data.slug or seo_service.generate_slug(post_data.title)

    # Check slug uniqueness
    existing = await db.execute(
        select(Post).where(Post.slug == slug)
    )
    if existing.scalar_one_or_none():
        import uuid as uuid_module
        slug = f"{slug}-{str(uuid_module.uuid4())[:8]}"

    # Create post
    new_post = Post(
        agent_id=post_data.agent_id,
        title=post_data.title,
        slug=slug,
        content=post_data.content,
        excerpt=post_data.excerpt,
        meta_title=post_data.meta_title,
        meta_description=post_data.meta_description,
        keywords=post_data.keywords or [],
        status=post_data.status,
        word_count=len(post_data.content.split()),
        tokens_used=0,
    )

    if post_data.status == "published":
        new_post.published_at = datetime.utcnow()

    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)

    return new_post


@router.get("", response_model=PostListResponse)
async def list_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    agent_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List posts with pagination and filtering."""
    query = select(Post)

    if status:
        query = query.where(Post.status == status)

    if agent_id:
        query = query.where(Post.agent_id == agent_id)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    query = query.order_by(Post.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    posts = result.scalars().all()

    return PostListResponse(
        items=posts,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get post by ID."""
    result = await db.execute(
        select(Post).where(Post.id == post_id)
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    return post


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: UUID,
    post_data: PostUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update post content and metadata."""
    result = await db.execute(
        select(Post).where(Post.id == post_id)
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    update_data = post_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(post, field, value)

    await db.commit()
    await db.refresh(post)

    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete post."""
    result = await db.execute(
        select(Post).where(Post.id == post_id)
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    await db.delete(post)
    await db.commit()


@router.post("/generate", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def generate_post(
    generate_data: PostGenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate blog post using AI.

    This endpoint:
    1. Validates agent exists
    2. Generates content using Claude API
    3. Calculates SEO metrics
    4. Saves post as draft
    """
    # Check agent exists
    result = await db.execute(
        select(Agent).where(Agent.id == generate_data.agent_id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    try:
        post_generator = get_post_generator()
        seo_service = SEOService()

        generation_result = await post_generator.generate_post(
            agent=agent,
            topic=generate_data.topic,
            keyword=generate_data.target_keyword,
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

        return new_post

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Post generation failed: {str(e)}",
        )


@router.post("/{post_id}/schedule")
async def schedule_post(
    post_id: UUID,
    schedule_data: PostScheduleRequest,
    db: AsyncSession = Depends(get_db),
):
    """Schedule post for future publication."""
    result = await db.execute(
        select(Post).where(Post.id == post_id)
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    post.status = "scheduled"
    post.scheduled_at = schedule_data.scheduled_at

    await db.commit()

    return {
        "message": "Post scheduled",
        "post_id": str(post_id),
        "scheduled_at": post.scheduled_at.isoformat()
    }


@router.post("/{post_id}/publish")
async def publish_post(
    post_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Publish post immediately."""
    result = await db.execute(
        select(Post).where(Post.id == post_id)
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    post.status = "published"
    post.published_at = datetime.utcnow()

    await db.commit()

    return {
        "message": "Post published",
        "post_id": str(post_id),
        "published_at": post.published_at.isoformat()
    }
