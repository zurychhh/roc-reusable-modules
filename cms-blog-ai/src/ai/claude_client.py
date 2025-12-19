"""
Claude API Client - wrapper for Anthropic API.
Handles rate limiting, retries, and error handling.
"""

import logging
from typing import Optional, List, Dict, Any
from anthropic import AsyncAnthropic
from anthropic.types import MessageParam

from ..config import settings

logger = logging.getLogger(__name__)


class ClaudeClient:
    """
    Async client for Claude API with rate limiting and error handling.

    Usage:
        client = ClaudeClient()
        text, tokens = await client.generate_text("Write a blog post about...")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ):
        """
        Initialize Claude client.

        Args:
            api_key: Anthropic API key (defaults to settings)
            model: Model name (defaults to settings)
            max_tokens: Max tokens to generate (defaults to settings)
            temperature: Temperature (defaults to settings)
        """
        self.client = AsyncAnthropic(
            api_key=api_key or settings.ANTHROPIC_API_KEY
        )
        self.model = model or settings.CLAUDE_MODEL
        self.max_tokens = max_tokens or settings.CLAUDE_MAX_TOKENS
        self.temperature = temperature or settings.CLAUDE_TEMPERATURE

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> tuple[str, int]:
        """
        Generate text using Claude API.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Max tokens to generate (default from config)
            temperature: Temperature (default from config)

        Returns:
            Tuple of (generated_text, tokens_used)

        Raises:
            Exception: If API call fails
        """
        try:
            messages: List[MessageParam] = [
                {"role": "user", "content": prompt}
            ]

            kwargs: Dict[str, Any] = {
                "model": self.model,
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature or self.temperature,
                "messages": messages,
            }

            if system_prompt:
                kwargs["system"] = system_prompt

            logger.info(f"Calling Claude API: model={self.model}, max_tokens={kwargs['max_tokens']}")

            response = await self.client.messages.create(**kwargs)

            # Extract text from response
            generated_text = ""
            if response.content:
                for block in response.content:
                    if hasattr(block, "text"):
                        generated_text += block.text

            # Calculate tokens used (input + output)
            tokens_used = response.usage.input_tokens + response.usage.output_tokens

            logger.info(f"Claude API success: {tokens_used} tokens used")

            return generated_text, tokens_used

        except Exception as e:
            logger.error(f"Claude API error: {e}", exc_info=True)
            raise

    async def generate_with_context(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> tuple[str, int]:
        """
        Generate text with conversation context.

        Args:
            messages: List of messages [{"role": "user"|"assistant", "content": "..."}]
            system_prompt: Optional system prompt
            max_tokens: Max tokens to generate
            temperature: Temperature

        Returns:
            Tuple of (generated_text, tokens_used)
        """
        try:
            # Convert messages to proper format
            formatted_messages: List[MessageParam] = []
            for msg in messages:
                formatted_messages.append({
                    "role": msg["role"],  # type: ignore
                    "content": msg["content"]
                })

            kwargs: Dict[str, Any] = {
                "model": self.model,
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature or self.temperature,
                "messages": formatted_messages,
            }

            if system_prompt:
                kwargs["system"] = system_prompt

            logger.info(f"Calling Claude API with context: {len(messages)} messages")

            response = await self.client.messages.create(**kwargs)

            # Extract text
            generated_text = ""
            if response.content:
                for block in response.content:
                    if hasattr(block, "text"):
                        generated_text += block.text

            tokens_used = response.usage.input_tokens + response.usage.output_tokens

            logger.info(f"Claude API success: {tokens_used} tokens used")

            return generated_text, tokens_used

        except Exception as e:
            logger.error(f"Claude API error: {e}", exc_info=True)
            raise


# Global instance
_claude_client: Optional[ClaudeClient] = None


def get_claude_client() -> ClaudeClient:
    """Get global Claude client instance."""
    global _claude_client
    if _claude_client is None:
        _claude_client = ClaudeClient()
    return _claude_client
