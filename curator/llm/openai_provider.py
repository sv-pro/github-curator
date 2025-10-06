"""OpenAI LLM provider."""

import os
from typing import Any, Optional

from curator.llm.base import BaseLLMProvider, LLMMessage, LLMResponse


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        base_url: Optional[str] = None,
    ):
        """Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model identifier
            base_url: Optional base URL (for compatible APIs)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.base_url = base_url

        # Lazy import to avoid requiring openai if not used
        try:
            import openai

            if base_url:
                self.client = openai.OpenAI(api_key=self.api_key, base_url=base_url)
            else:
                self.client = openai.OpenAI(api_key=self.api_key)
        except ImportError as err:
            raise ImportError(
                "OpenAI provider requires the 'openai' package. "
                "Install it with: pip install openai"
            ) from err

    def complete(
        self,
        messages: list[LLMMessage],
        max_tokens: int = 2000,
        temperature: float = 1.0,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate completion using OpenAI."""
        # Convert messages to OpenAI format
        openai_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs,
        )

        usage = {
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }

        return LLMResponse(
            content=response.choices[0].message.content,
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
        return "openai"
