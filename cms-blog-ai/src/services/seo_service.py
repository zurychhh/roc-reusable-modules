"""
SEO Service - SEO analysis and optimization utilities.
"""

import re
from typing import List, Dict
from unicodedata import normalize


class SEOService:
    """
    SEO analysis and optimization service.

    Provides:
    - Readability score calculation (Flesch-Kincaid)
    - Keyword density analysis
    - Slug generation
    - Schema.org markup generation
    """

    def calculate_readability_score(self, content: str) -> float:
        """
        Calculate Flesch-Kincaid readability score.

        Higher scores = easier to read
        - 90-100: Very easy (5th grade)
        - 80-89: Easy (6th grade)
        - 70-79: Fairly easy (7th grade)
        - 60-69: Standard (8th-9th grade)
        - 50-59: Fairly difficult (10th-12th grade)
        - 30-49: Difficult (college)
        - 0-29: Very difficult (graduate)

        Args:
            content: Text content (HTML tags will be stripped)

        Returns:
            Readability score (0-100+)
        """
        # Strip HTML tags
        text = re.sub(r'<[^>]+>', '', content)

        # Count sentences (. ! ?)
        sentences = len(re.findall(r'[.!?]+', text))
        if sentences == 0:
            sentences = 1

        # Count words
        words = len(text.split())
        if words == 0:
            return 0

        # Count syllables (approximation for English)
        syllables = self._count_syllables(text)

        # Flesch Reading Ease formula
        # 206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/words)
        score = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)

        # Clamp to reasonable range
        return max(0, min(100, score))

    def _count_syllables(self, text: str) -> int:
        """
        Count syllables in text (approximation).

        Uses vowel counting with common exceptions.
        """
        text = text.lower()
        words = text.split()
        total_syllables = 0

        for word in words:
            word = re.sub(r'[^a-z]', '', word)
            if not word:
                continue

            # Count vowels
            syllables = len(re.findall(r'[aeiouy]+', word))

            # Subtract silent e at end
            if word.endswith('e') and syllables > 1:
                syllables -= 1

            # Ensure at least 1 syllable
            syllables = max(1, syllables)
            total_syllables += syllables

        return total_syllables

    def calculate_keyword_density(
        self,
        content: str,
        keywords: List[str]
    ) -> Dict[str, float]:
        """
        Calculate keyword density for each keyword.

        Density = (keyword occurrences / total words) * 100

        Optimal density is typically 1-3%.

        Args:
            content: Text content
            keywords: List of keywords to check

        Returns:
            Dict mapping keyword to density percentage
        """
        # Strip HTML and normalize
        text = re.sub(r'<[^>]+>', '', content).lower()
        words = text.split()
        total_words = len(words)

        if total_words == 0:
            return {}

        density = {}
        for keyword in keywords:
            keyword_lower = keyword.lower()
            # Count occurrences (including partial matches for phrases)
            count = text.count(keyword_lower)
            density[keyword] = round((count / total_words) * 100, 2)

        return density

    def generate_slug(self, title: str) -> str:
        """
        Generate URL-friendly slug from title.

        Args:
            title: Post title

        Returns:
            URL-safe slug
        """
        # Normalize unicode
        slug = normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')

        # Convert to lowercase
        slug = slug.lower()

        # Replace spaces and special chars with hyphens
        slug = re.sub(r'[^a-z0-9]+', '-', slug)

        # Remove leading/trailing hyphens
        slug = slug.strip('-')

        # Limit length
        if len(slug) > 100:
            slug = slug[:100].rsplit('-', 1)[0]

        return slug

    def generate_schema_markup(
        self,
        post_title: str,
        post_content: str,
        author_name: str,
        published_at: str = None,
        site_name: str = "Blog",
        site_url: str = "https://example.com"
    ) -> dict:
        """
        Generate Schema.org Article markup.

        Args:
            post_title: Article title
            post_content: Article content (excerpt will be generated)
            author_name: Author name
            published_at: Publication date (ISO format)
            site_name: Website name
            site_url: Website URL

        Returns:
            Schema.org JSON-LD object
        """
        # Generate excerpt (first 200 chars)
        excerpt = re.sub(r'<[^>]+>', '', post_content)[:200]
        if len(post_content) > 200:
            excerpt += "..."

        schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": post_title[:110],  # Max 110 chars
            "description": excerpt,
            "author": {
                "@type": "Person",
                "name": author_name
            },
            "publisher": {
                "@type": "Organization",
                "name": site_name,
                "url": site_url
            }
        }

        if published_at:
            schema["datePublished"] = published_at

        return schema
