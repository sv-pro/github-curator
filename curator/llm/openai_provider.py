"""OpenAI LLM provider."""

import os
from typing import Any, Optional

from curator.errors import (
    LLMAPIError,
    LLMAuthenticationError,
    LLMModelError,
    LLMRateLimitError,
    LLMTimeoutError,
)
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
        if not self.api_key:
            raise LLMAuthenticationError(
                provider="openai",
                message="OpenAI API key required",
                details={
                    "solution": "Set OPENAI_API_KEY environment variable or pass api_key parameter"
                },
            )
        self.model = model
        self.base_url = base_url

        # Lazy import to avoid requiring openai if not used
        try:
            import openai

            self.openai = openai  # Store module for exception handling
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

        try:
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
        except self.openai.AuthenticationError as e:
            raise LLMAuthenticationError(
                provider="openai",
                message=f"Authentication failed: {e}",
                details={"model": self.model},
            ) from e
        except self.openai.RateLimitError as e:
            raise LLMRateLimitError(
                provider="openai",
                details={"model": self.model, "message": str(e)},
            ) from e
        except self.openai.APITimeoutError as e:
            raise LLMTimeoutError(
                provider="openai",
                timeout=60,
                details={"model": self.model, "message": str(e)},
            ) from e
        except self.openai.NotFoundError as e:
            raise LLMModelError(
                provider="openai",
                model=self.model,
                message=f"Model not found: {e}",
            ) from e
        except self.openai.BadRequestError as e:
            error_message = str(e)
            if "context" in error_message.lower() or "token" in error_message.lower():
                raise LLMModelError(
                    provider="openai",
                    model=self.model,
                    message=f"Model limit exceeded: {error_message}",
                ) from e
            raise LLMAPIError(
                provider="openai",
                message=f"Bad request: {error_message}",
                details={"model": self.model},
            ) from e
        except self.openai.APIError as e:
            raise LLMAPIError(
                provider="openai",
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
        return "openai"
