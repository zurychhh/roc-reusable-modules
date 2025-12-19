"""
Pydantic schemas for agents.
"""

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any


class AgentCreate(BaseModel):
    """Create agent schema."""
    name: str = Field(..., min_length=1, max_length=255)
    expertise: str = Field(..., min_length=1, max_length=100)
    persona: Optional[str] = None
    tone: str = Field("professional", pattern="^(professional|casual|friendly|formal)$")
    post_length: str = Field("medium", pattern="^(short|medium|long|very_long)$")
    schedule_cron: Optional[str] = None
    workflow: str = Field("draft", pattern="^(draft|auto|scheduled)$")
    settings: Optional[Dict[str, Any]] = None


class AgentUpdate(BaseModel):
    """Update agent schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    expertise: Optional[str] = Field(None, min_length=1, max_length=100)
    persona: Optional[str] = None
    tone: Optional[str] = Field(None, pattern="^(professional|casual|friendly|formal)$")
    post_length: Optional[str] = Field(None, pattern="^(short|medium|long|very_long)$")
    schedule_cron: Optional[str] = None
    workflow: Optional[str] = Field(None, pattern="^(draft|auto|scheduled)$")
    is_active: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    """Agent response schema."""
    id: UUID
    name: str
    expertise: str
    persona: Optional[str]
    tone: str
    post_length: str
    schedule_cron: Optional[str]
    workflow: str
    is_active: bool
    settings: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
