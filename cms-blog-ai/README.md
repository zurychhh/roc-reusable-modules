# CMS Blog AI Module

A reusable Python module for AI-powered blog content management. Enables manual post creation, AI-assisted content generation via Claude API, and **automated scheduling** for hands-free blog management.

## Features

- **Manual Post Creation** - Traditional blog post CRUD operations with SEO metadata
- **AI Content Generation** - Generate blog posts using Anthropic's Claude API with customizable personas
- **Automated Scheduler** - Cron-based scheduling for automatic post generation (the killer feature!)
- **Agent System** - Configure multiple AI "personas" with different expertise and writing styles
- **SEO Optimization** - Built-in readability scoring, keyword density analysis, and schema.org markup
- **Async Architecture** - Full async/await support with FastAPI and SQLAlchemy

## Requirements

- Python 3.10+
- PostgreSQL 14+
- Redis 6+ (for Celery task queue)
- Anthropic API key (Claude)

## Installation

### 1. Copy Module to Your Project

```bash
# Clone or copy the cms-blog-ai directory to your project
cp -r cms-blog-ai /path/to/your/project/
```

### 2. Install Dependencies

```bash
pip install -r cms-blog-ai/requirements.txt
```

Or install individually:
```bash
pip install fastapi uvicorn sqlalchemy[asyncio] asyncpg
pip install anthropic celery[redis] redis croniter
pip install pydantic pydantic-settings python-dotenv
```

### 3. Configure Environment Variables

Create a `.env` file in your project root:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/cms_blog

# Redis/Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Claude API (REQUIRED)
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Optional: Model configuration
CLAUDE_MODEL=claude-sonnet-4-20250514
CLAUDE_MAX_TOKENS=4096
CLAUDE_TEMPERATURE=0.7

# Scheduler
SCHEDULER_CHECK_INTERVAL_MINUTES=5
```

### 4. Initialize Database

```python
# Run this once to create tables
from cms_blog_ai.src.database import engine, Base

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

import asyncio
asyncio.run(init_db())
```

Or use Alembic migrations (recommended for production).

## Quick Start

### 1. Register API Routes

```python
# main.py
from fastapi import FastAPI
from cms_blog_ai.src.api import posts_router, agents_router, schedules_router

app = FastAPI(title="My Blog API")

# Mount CMS Blog AI routers
app.include_router(posts_router, prefix="/api/v1")
app.include_router(agents_router, prefix="/api/v1")
app.include_router(schedules_router, prefix="/api/v1")
```

### 2. Start the API Server

```bash
uvicorn main:app --reload
```

### 3. Start Celery Worker (for async tasks)

```bash
celery -A cms_blog_ai.src.tasks.celery_app worker --loglevel=info
```

### 4. Start Celery Beat (for scheduler)

```bash
celery -A cms_blog_ai.src.tasks.celery_app beat --loglevel=info
```

## API Reference

### Agents

Agents are AI personas that generate content with specific expertise and writing styles.

#### Create Agent
```bash
POST /api/v1/agents
Content-Type: application/json

{
  "name": "Legal Expert",
  "expertise": "Polish civil law, consumer rights, GDPR",
  "persona": "You are a helpful legal expert specializing in Polish law.",
  "tone": "professional",
  "post_length": "long",
  "workflow": "draft"
}
```

#### List Agents
```bash
GET /api/v1/agents?page=1&page_size=20&is_active=true
```

#### Get Agent
```bash
GET /api/v1/agents/{agent_id}
```

#### Update Agent
```bash
PUT /api/v1/agents/{agent_id}
Content-Type: application/json

{
  "name": "Updated Legal Expert",
  "tone": "friendly"
}
```

#### Delete Agent
```bash
DELETE /api/v1/agents/{agent_id}
```

#### Trigger Manual Generation
```bash
POST /api/v1/agents/{agent_id}/generate?topic=GDPR%20compliance&keyword=data%20protection
```

### Posts

#### Create Post (Manual)
```bash
POST /api/v1/posts
Content-Type: application/json

{
  "agent_id": "uuid-here",
  "title": "Understanding GDPR",
  "content": "<h1>Understanding GDPR</h1><p>Content here...</p>",
  "excerpt": "A comprehensive guide to GDPR compliance",
  "meta_title": "GDPR Guide 2024",
  "meta_description": "Learn about GDPR requirements...",
  "keywords": ["gdpr", "data protection", "privacy"],
  "status": "draft"
}
```

#### Generate Post with AI
```bash
POST /api/v1/posts/generate
Content-Type: application/json

{
  "agent_id": "uuid-here",
  "topic": "Understanding consumer rights in online purchases",
  "target_keyword": "consumer rights"
}
```

#### List Posts
```bash
GET /api/v1/posts?page=1&page_size=20&status=draft&agent_id=uuid
```

#### Get Post
```bash
GET /api/v1/posts/{post_id}
```

#### Update Post
```bash
PUT /api/v1/posts/{post_id}
Content-Type: application/json

{
  "title": "Updated Title",
  "status": "published"
}
```

#### Delete Post
```bash
DELETE /api/v1/posts/{post_id}
```

#### Schedule Post
```bash
POST /api/v1/posts/{post_id}/schedule
Content-Type: application/json

{
  "scheduled_at": "2024-12-25T10:00:00Z"
}
```

#### Publish Post Immediately
```bash
POST /api/v1/posts/{post_id}/publish
```

### Schedules (The Key Feature!)

Schedules enable automatic post generation at configured intervals.

#### Create Schedule
```bash
POST /api/v1/schedules
Content-Type: application/json

{
  "agent_id": "uuid-here",
  "interval": "daily",
  "publish_hour": 9,
  "timezone": "Europe/Warsaw",
  "auto_publish": false,
  "target_keywords": ["legal", "consumer", "rights"],
  "post_length": "medium"
}
```

**Available intervals:**
- `daily` - Every day at specified hour
- `every_3_days` - Every 3 days
- `weekly` - Every Monday
- `biweekly` - 1st and 15th of each month

#### List Schedules
```bash
GET /api/v1/schedules?page=1&is_active=true
```

#### Get Schedule
```bash
GET /api/v1/schedules/{schedule_id}
```

#### Update Schedule
```bash
PUT /api/v1/schedules/{schedule_id}
Content-Type: application/json

{
  "interval": "weekly",
  "publish_hour": 14
}
```

#### Delete Schedule
```bash
DELETE /api/v1/schedules/{schedule_id}
```

#### Activate Schedule
```bash
POST /api/v1/schedules/{schedule_id}/activate
```

#### Deactivate Schedule
```bash
POST /api/v1/schedules/{schedule_id}/deactivate
```

## Scheduler Deep Dive

The scheduler is the most powerful feature of this module. Here's how it works:

### Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Celery Beat    │────▶│  Redis Queue    │────▶│  Celery Worker  │
│  (every 5 min)  │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                                               │
         │                                               ▼
         │                                      ┌─────────────────┐
         │                                      │  Claude API     │
         │                                      │  (generate)     │
         │                                      └─────────────────┘
         │                                               │
         ▼                                               ▼
┌─────────────────┐                            ┌─────────────────┐
│  PostgreSQL     │◀───────────────────────────│  Save Post      │
│  (schedules)    │                            │  (draft/publish)│
└─────────────────┘                            └─────────────────┘
```

### How It Works

1. **Celery Beat** runs `process_agent_schedules` task every 5 minutes (configurable)
2. The task queries all **active agents with schedules**
3. For each agent, it parses the **cron expression** and checks if it should have run
4. If due, it triggers `generate_post_for_agent` async task
5. The worker generates content via **Claude API**
6. Post is saved as **draft** (or auto-published if configured)
7. Schedule statistics are updated (total/successful/failed counts)

### Cron Expression Mapping

| Interval      | Cron Expression          | Description                |
|---------------|--------------------------|----------------------------|
| `daily`       | `0 {hour} * * *`         | Daily at specified hour    |
| `every_3_days`| `0 {hour} */3 * *`       | Every 3 days              |
| `weekly`      | `0 {hour} * * 1`         | Every Monday              |
| `biweekly`    | `0 {hour} 1,15 * *`      | 1st and 15th of month     |

### Running the Scheduler

**Development (single terminal):**
```bash
# Worker + Beat in one process
celery -A cms_blog_ai.src.tasks.celery_app worker --beat --loglevel=info
```

**Production (separate processes):**
```bash
# Terminal 1: Worker
celery -A cms_blog_ai.src.tasks.celery_app worker --loglevel=info --concurrency=4

# Terminal 2: Beat
celery -A cms_blog_ai.src.tasks.celery_app beat --loglevel=info
```

**Docker Compose:**
```yaml
services:
  celery-worker:
    build: .
    command: celery -A cms_blog_ai.src.tasks.celery_app worker --loglevel=info
    depends_on:
      - redis
      - postgres

  celery-beat:
    build: .
    command: celery -A cms_blog_ai.src.tasks.celery_app beat --loglevel=info
    depends_on:
      - redis
      - postgres
```

## Customization

### Custom Prompts

Edit `src/ai/prompts.py` to customize the AI generation:

```python
# HTML Components for generated content
HTML_COMPONENTS = """
<info-box>...</info-box>
<tip-box>...</tip-box>
...
"""

# System prompt builder
def build_system_prompt(agent: Agent) -> str:
    return f"""
    You are {agent.name}, an expert in {agent.expertise}.
    Your persona: {agent.persona}
    Writing tone: {agent.tone}
    ...
    """
```

### Custom Post Lengths

Modify word count targets in `src/ai/prompts.py`:

```python
POST_LENGTH_MAP = {
    "short": (300, 500),      # 300-500 words
    "medium": (600, 900),     # 600-900 words
    "long": (1000, 1500),     # 1000-1500 words
    "very_long": (1500, 2500) # 1500-2500 words
}
```

### Custom Schedule Intervals

Add new intervals in `src/models/schedule.py`:

```python
class ScheduleInterval(str, Enum):
    DAILY = "daily"
    EVERY_3_DAYS = "every_3_days"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"  # Add new interval

INTERVAL_CRON_MAP = {
    # ... existing mappings
    ScheduleInterval.MONTHLY: "0 {hour} 1 * *",  # 1st of each month
}
```

## Database Models

### Post
```python
class Post:
    id: UUID
    agent_id: UUID
    title: str
    slug: str
    content: str  # HTML content
    excerpt: str
    meta_title: str
    meta_description: str
    keywords: List[str]
    status: Enum["draft", "scheduled", "published", "failed"]
    scheduled_at: datetime
    published_at: datetime
    tokens_used: int
    word_count: int
    readability_score: float
    keyword_density: dict
    created_at: datetime
    updated_at: datetime
```

### Agent
```python
class Agent:
    id: UUID
    name: str
    expertise: str
    persona: str
    tone: Enum["professional", "friendly", "casual", "formal"]
    post_length: Enum["short", "medium", "long", "very_long"]
    schedule_cron: str  # Cron expression for scheduler
    workflow: Enum["draft", "auto", "scheduled"]
    settings: dict  # Custom settings JSON
    is_active: bool
    total_posts: int
    created_at: datetime
    updated_at: datetime
```

### ScheduleConfig
```python
class ScheduleConfig:
    id: UUID
    agent_id: UUID
    interval: ScheduleInterval
    publish_hour: int  # 0-23
    timezone: str
    is_active: bool
    auto_publish: bool
    target_keywords: List[str]
    exclude_keywords: List[str]
    post_length: str
    total_posts_generated: int
    successful_posts: int
    failed_posts: int
    last_run_at: datetime
    next_run_at: datetime
    created_at: datetime
    updated_at: datetime
```

## SEO Features

### Readability Score

Uses Flesch-Kincaid formula:
- 90-100: Very easy (5th grade)
- 80-89: Easy (6th grade)
- 70-79: Fairly easy (7th grade)
- 60-69: Standard (8th-9th grade)
- 50-59: Fairly difficult (10th-12th grade)

### Keyword Density

Calculates percentage of keyword occurrences:
```python
density = (keyword_count / total_words) * 100
# Optimal: 1-3%
```

### Schema.org Markup

Generates Article schema for SEO:
```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Post Title",
  "description": "Post excerpt...",
  "author": { "@type": "Person", "name": "Agent Name" },
  "datePublished": "2024-01-01T00:00:00Z"
}
```

## Troubleshooting

### Celery Worker Not Starting
```bash
# Check Redis connection
redis-cli ping

# Check Celery configuration
celery -A cms_blog_ai.src.tasks.celery_app inspect active
```

### Posts Not Being Generated
1. Check agent has `is_active=true`
2. Check schedule has `is_active=true`
3. Verify `ANTHROPIC_API_KEY` is set
4. Check Celery Beat is running
5. Check worker logs for errors

### Database Connection Issues
```bash
# Test PostgreSQL connection
psql -h localhost -U postgres -d cms_blog -c "SELECT 1"

# Check async driver
pip show asyncpg
```

### Claude API Errors
- Verify API key is valid
- Check rate limits
- Ensure model name is correct (`claude-sonnet-4-20250514`)

## Directory Structure

```
cms-blog-ai/
├── src/
│   ├── __init__.py
│   ├── config.py           # Pydantic settings
│   ├── database.py         # Async SQLAlchemy setup
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── post.py         # Post model
│   │   ├── agent.py        # Agent model
│   │   └── schedule.py     # ScheduleConfig model
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── post.py         # Post Pydantic schemas
│   │   ├── agent.py        # Agent schemas
│   │   └── schedule.py     # Schedule schemas
│   │
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── claude_client.py    # Anthropic API wrapper
│   │   ├── prompts.py          # Prompt templates
│   │   └── post_generator.py   # Generation orchestrator
│   │
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── celery_app.py       # Celery configuration
│   │   └── post_tasks.py       # Scheduler tasks
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   └── seo_service.py      # SEO utilities
│   │
│   └── api/
│       ├── __init__.py
│       ├── posts.py            # Posts API
│       ├── agents.py           # Agents API
│       └── schedules.py        # Schedules API
│
├── examples/
│   └── sveltekit/              # SvelteKit integration example
│
├── requirements.txt
├── .env.example
├── docker-compose.yml
└── README.md
```

## License

MIT License - See main repository for details.

## Contributing

Contributions are welcome! Please read the main repository's contributing guidelines.
