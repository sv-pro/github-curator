"""Anthropic Claude LLM provider."""

import os
from typing import Any, Optional

import anthropic

from curator.errors import (
    LLMAPIError,
    LLMAuthenticationError,
    LLMModelError,
    LLMRateLimitError,
    LLMTimeoutError,
)
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
        if not self.api_key:
            raise LLMAuthenticationError(
                provider="anthropic",
                message="Anthropic API key required",
                details={
                    "solution": "Set ANTHROPIC_API_KEY environment variable or pass api_key parameter"
                },
            )
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

        try:
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
        except anthropic.AuthenticationError as e:
            raise LLMAuthenticationError(
                provider="anthropic",
                message=f"Authentication failed: {e}",
                details={"model": self.model},
            ) from e
        except anthropic.RateLimitError as e:
            raise LLMRateLimitError(
                provider="anthropic",
                details={"model": self.model, "message": str(e)},
            ) from e
        except anthropic.APITimeoutError as e:
            raise LLMTimeoutError(
                provider="anthropic",
                timeout=60,  # Default timeout
                details={"model": self.model, "message": str(e)},
            ) from e
        except anthropic.BadRequestError as e:
            # Handle model-specific errors (not found, context length, etc)
            error_message = str(e)
            if "model" in error_message.lower():
                raise LLMModelError(
                    provider="anthropic",
                    model=self.model,
                    message=f"Model error: {error_message}",
                ) from e
            raise LLMAPIError(
                provider="anthropic",
                message=f"Bad request: {error_message}",
                details={"model": self.model},
            ) from e
        except anthropic.APIError as e:
            raise LLMAPIError(
                provider="anthropic",
                message=f"API error: {e}",
                status_code=getattr(e, "status_code", None),
                details={"model": self.model},
            ) from e

    def get_model_name(self) -> str:
        """Get model identifier."""
        return self.model

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "anthropic"
