"""
CMS Blog AI - Configuration Module
Pydantic Settings with environment variable loading.

Customize these settings for your project by:
1. Setting environment variables
2. Creating a .env file
3. Overriding defaults in your own config subclass
"""

from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class CMSBlogSettings(BaseSettings):
    """
    CMS Blog AI Settings.

    All settings can be overridden via environment variables.
    Prefix: CMS_BLOG_ (optional, customize in your subclass)
    """

    # Application
    APP_NAME: str = "CMS Blog AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"

    # Database (PostgreSQL)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/cms_blog"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis (for Celery and caching)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # JWT Authentication
    JWT_SECRET: str = "change-this-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 24

    # Password hashing
    PASSWORD_MIN_LENGTH: int = 8
    BCRYPT_ROUNDS: int = 12

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # Claude API (Anthropic) - REQUIRED
    ANTHROPIC_API_KEY: str = ""  # Set via environment variable
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"
    CLAUDE_MAX_TOKENS: int = 4000
    CLAUDE_TEMPERATURE: float = 0.7

    # Usage Limits (per tenant/user)
    DEFAULT_TOKENS_LIMIT: int = 100000
    DEFAULT_POSTS_LIMIT: int = 50

    # Frontend URL (for CORS)
    FRONTEND_URL: str = "http://localhost:5173"

    # Logging
    LOG_LEVEL: str = "INFO"

    # Content Settings
    DEFAULT_POST_LENGTH: str = "medium"  # short, medium, long, very_long
    DEFAULT_TONE: str = "professional"  # professional, casual, friendly

    # Scheduler Settings
    SCHEDULER_CHECK_INTERVAL_MINUTES: int = 5  # How often to check for scheduled posts

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance - import this in your app
settings = CMSBlogSettings()


def get_settings() -> CMSBlogSettings:
    """Get settings instance. Use this for dependency injection."""
    return settings
