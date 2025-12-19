"""
Prompt templates for AI content generation.
Structured prompts for blog posts, SEO metadata, etc.

CUSTOMIZATION:
- Modify HTML_COMPONENTS to add your own styled components
- Override build_system_prompt() for custom persona configuration
- Adjust word counts in build_post_generation_prompt() as needed
"""

from typing import Optional


# HTML component templates for AI to use
# Customize these CSS classes to match your frontend styling
HTML_COMPONENTS = """
=== AVAILABLE HTML COMPONENTS ===

1. INFO-BOX (important information):
<div class="info-box blue">
<div class="info-box-title"><i class="fas fa-info-circle"></i> Title</div>
<p>Content here.</p>
</div>
Colors: blue (info), yellow (warning), green (success), orange (caution)
Icons: fa-info-circle, fa-lightbulb (tip), fa-exclamation-triangle (warning), fa-clock (deadline)

2. HIGHLIGHT-BOX (key data/statistics):
<div class="highlight-box">
<div class="highlight-grid">
<div class="highlight-item">
<span class="highlight-label">Label</span>
<span class="highlight-value">Value</span>
</div>
</div>
</div>

3. CARD-GRID (side-by-side cards):
<div class="card-grid">
<div class="info-card">
<h3><i class="fas fa-icon"></i> Card Title</h3>
<p>Card content.</p>
</div>
</div>

4. TWO-COLUMNS (comparisons, pros/cons):
<div class="two-columns">
<div class="column">
<h4 class="column-title green"><i class="fas fa-check-circle"></i> Pros</h4>
<ul><li>Item</li></ul>
</div>
<div class="column">
<h4 class="column-title orange"><i class="fas fa-exclamation-circle"></i> Cons</h4>
<ul><li>Item</li></ul>
</div>
</div>

5. TIPS-LIST (step-by-step tips):
<div class="tips-list">
<div class="tip-item">
<span class="tip-number">1</span>
<div class="tip-content">
<strong>Step title</strong>
<p>Step description.</p>
</div>
</div>
</div>

6. SECTION-DIVIDER:
<hr class="section-divider" />

7. DISCLAIMER-BOX (legal disclaimer at end):
<div class="disclaimer-box">
<p><strong>Disclaimer:</strong> This article is for informational purposes only.</p>
</div>
"""


def build_system_prompt(
    expertise: str,
    persona: Optional[str] = None,
    tone: str = "professional",
    target_audience: Optional[str] = None,
    language: str = "English"
) -> str:
    """
    Build system prompt for Claude based on agent configuration.

    Args:
        expertise: Domain expertise (e.g., "technology", "marketing", "law")
        persona: Agent persona description
        tone: Writing tone (professional, casual, friendly)
        target_audience: Optional target audience description
        language: Content language (default: English)

    Returns:
        System prompt string
    """
    prompt = f"""You are an expert in: {expertise}"""

    if persona:
        prompt += f"\n\nYour persona:\n{persona}"

    prompt += f"\n\nWriting tone: {tone}"
    prompt += f"\nContent language: {language}"

    if target_audience:
        prompt += f"\nTarget audience: {target_audience}"

    prompt += """

WRITING RULES:

1. **SEO Structure:**
   - Use HTML heading hierarchy (<h2>, <h3>)
   - Include main keyword in first 100 words
   - Keep paragraphs to 3-4 sentences for readability
   - Use lists <ul>/<li> for better scanning

2. **Content Quality:**
   - Write naturally, avoid keyword stuffing
   - Use synonyms and related terms
   - Include specific examples and data
   - Cite sources where possible

3. **Engagement:**
   - Start with a strong hook
   - Use rhetorical questions
   - Add practical tips
   - End with clear summary

4. **Format - IMPORTANT:**
   - Write in clean HTML (NOT Markdown!)
   - Use <strong> for key points
   - Use <em> for emphasis
   - DO NOT use # or ** - that's Markdown!
   - Use special HTML components below
"""

    prompt += HTML_COMPONENTS

    return prompt


def build_post_generation_prompt(
    topic: str,
    keyword: Optional[str] = None,
    length: str = "medium",
    sources_content: Optional[str] = None,
    additional_context: Optional[str] = None,
    language: str = "English"
) -> str:
    """
    Build prompt for blog post generation.

    Args:
        topic: Post topic/title
        keyword: Target SEO keyword
        length: Post length (short/medium/long/very_long)
        sources_content: Optional source content to reference
        additional_context: Optional additional context
        language: Content language

    Returns:
        Generation prompt string
    """
    # Word count targets
    word_counts = {
        "short": "500-700",
        "medium": "1000-1500",
        "long": "2000-3000",
        "very_long": "3000-5000"
    }
    target_words = word_counts.get(length, "1000-1500")

    prompt = f"""Write a professional blog article about:

TOPIC: {topic}
LANGUAGE: {language}"""

    if keyword:
        prompt += f"\nMAIN SEO KEYWORD: {keyword}"

    prompt += f"""
TARGET LENGTH: {target_words} words
FORMAT: Clean HTML with CSS components (NOT Markdown!)

"""

    if sources_content:
        prompt += f"""SOURCES TO USE:
{sources_content}

Use these sources as inspiration and facts, but write in your own words.

"""

    if additional_context:
        prompt += f"""ADDITIONAL CONTEXT:
{additional_context}

"""

    prompt += """REQUIRED HTML STRUCTURE:

1. SECTIONS (3-5 sections with <h2>):
   - Each section focused on one aspect
   - Separate sections with: <hr class="section-divider" />
   - Use <h3> for subsections
   - Use <ul><li> for lists

2. VISUAL ELEMENTS (use at least 3-4 different):
   - highlight-box for key data/statistics
   - card-grid for comparing options
   - two-columns for pros/cons
   - tips-list for step-by-step guides
   - info-box yellow for warnings
   - info-box green for positive notes

3. AT THE END - ALWAYS add disclaimer-box:
<div class="disclaimer-box">
<p><strong>Disclaimer:</strong> This article is for informational purposes only and does not constitute professional advice.</p>
</div>

IMPORTANT RULES:
- Write in clean HTML, DO NOT use Markdown (no # or **)
- Use <strong> instead of **text**
- Use <h2> instead of ## Heading
- Use <p> for paragraphs
- DO NOT start with <h1> - title is separate
- Start with intro <p> or an info-box
- Introduce keyword naturally in content
- Write accessibly but professionally
"""

    return prompt


def build_meta_title_prompt(content: str, keyword: Optional[str] = None) -> str:
    """
    Build prompt for meta title generation.

    Args:
        content: Post content
        keyword: Target keyword

    Returns:
        Prompt for meta title
    """
    prompt = f"""Based on the following article, generate an SEO-friendly meta title.

**Requirements:**
- Maximum 60 characters
- Contains main keyword: {keyword if keyword else "extract from content"}
- Attention-grabbing
- Clearly communicates topic
- No clickbait

**Article:**
{content[:1000]}...

Respond with ONLY the title, no quotes or additional text."""

    return prompt


def build_meta_description_prompt(content: str, keyword: Optional[str] = None) -> str:
    """
    Build prompt for meta description generation.

    Args:
        content: Post content
        keyword: Target keyword

    Returns:
        Prompt for meta description
    """
    prompt = f"""Based on the following article, generate an SEO-friendly meta description.

**Requirements:**
- Maximum 160 characters
- Contains main keyword: {keyword if keyword else "extract from content"}
- Encourages click-through
- Clearly communicates article value
- Ends with CTA or incentive

**Article:**
{content[:1000]}...

Respond with ONLY the description, no quotes or additional text."""

    return prompt


def build_keywords_extraction_prompt(content: str) -> str:
    """
    Build prompt for keyword extraction.

    Args:
        content: Post content

    Returns:
        Prompt for keyword extraction
    """
    prompt = f"""Analyze the following article and extract 5-10 most important keywords.

**Requirements:**
- 1-3 word phrases
- Relevant for SEO
- Natural to the content
- Sorted by importance

**Article:**
{content[:2000]}...

Respond in JSON array format, e.g.: ["keyword1", "keyword2", "keyword3"]
ONLY JSON, no additional text."""

    return prompt
