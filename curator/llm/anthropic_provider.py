"""Anthropic Claude LLM provider."""

import os
from typing import Any, Optional

import anthropic

from curator.llm.base import BaseLLMProvider, LLMMessage, LLMResponse


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude API provider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-5-20250929",
    ):
        """Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Model identifier
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def complete(
        self,
        messages: list[LLMMessage],
        max_tokens: int = 2000,
        temperature: float = 1.0,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate completion using Claude."""
        # Convert messages to Anthropic format
        anthropic_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=anthropic_messages,
            **kwargs,
        )

        usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }

        return LLMResponse(
            content=response.content[0].text,
            model=response.model,
            usage=usage,
            raw_response=response,
        )

    def get_model_name(self) -> str:
        """Get model identifier."""
        return self.model

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "anthropic"
