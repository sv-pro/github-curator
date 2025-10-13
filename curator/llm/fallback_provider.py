"""Fallback LLM provider with automatic provider chain retry logic."""

import logging
from typing import Any, Optional

from curator.errors import LLMQuotaExceededError, LLMRateLimitError
from curator.llm.base import BaseLLMProvider, LLMMessage, LLMResponse

logger = logging.getLogger(__name__)


class FallbackLLMProvider(BaseLLMProvider):
    """LLM provider that tries a chain of providers on failure.

    This wrapper attempts to use providers in sequence, falling back to the next
    provider if the current one fails with quota/rate limit errors.

    Example:
        # Try Anthropic first, fall back to OpenAI, then Ollama
        provider = FallbackLLMProvider(
            providers=[anthropic_provider, openai_provider, ollama_provider]
        )

        # Will try anthropic first, if credit balance error occurs,
        # automatically switch to openai, then ollama
        response = provider.complete(messages)
    """

    def __init__(self, providers: list[BaseLLMProvider]):
        """Initialize fallback provider.

        Args:
            providers: List of providers to try in order
        """
        if not providers:
            raise ValueError("At least one provider must be specified")

        self.providers = providers
        self._current_provider_index = 0
        self._exhausted_providers: set[int] = set()

    @property
    def current_provider(self) -> BaseLLMProvider:
        """Get the currently active provider."""
        return self.providers[self._current_provider_index]

    def complete(
        self,
        messages: list[LLMMessage],
        max_tokens: int = 2000,
        temperature: float = 1.0,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate completion with automatic fallback on quota/rate limit errors.

        Args:
            messages: List of conversation messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-2)
            **kwargs: Provider-specific additional parameters

        Returns:
            LLMResponse from the first successful provider

        Raises:
            Exception: If all providers fail
        """
        last_exception: Optional[Exception] = None

        # Try each provider in sequence
        for idx, provider in enumerate(self.providers):
            # Skip exhausted providers
            if idx in self._exhausted_providers:
                logger.debug(f"Skipping exhausted provider: {provider.provider_name}")
                continue

            try:
                logger.info(
                    f"Attempting LLM completion with provider: {provider.provider_name} "
                    f"(model: {provider.get_model_name()})"
                )

                response = provider.complete(
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs,
                )

                # Success! Update current provider and return
                if self._current_provider_index != idx:
                    logger.info(f"Successfully failed over to provider: {provider.provider_name}")
                    self._current_provider_index = idx

                return response

            except (LLMQuotaExceededError, LLMRateLimitError) as e:
                # Provider exhausted or rate limited - mark and try next
                logger.warning(
                    f"Provider {provider.provider_name} failed: {e.message}. "
                    f"Trying next provider in chain..."
                )
                self._exhausted_providers.add(idx)
                last_exception = e
                continue

            except Exception as e:
                # Other errors - log but still try next provider
                logger.error(
                    f"Provider {provider.provider_name} error: {type(e).__name__}: {e}. "
                    f"Trying next provider..."
                )
                last_exception = e
                continue

        # All providers failed
        providers_str = ", ".join(p.provider_name for p in self.providers)
        error_msg = f"All providers exhausted ({providers_str})"
        if last_exception:
            error_msg += f". Last error: {last_exception}"

        logger.error(error_msg)
        if last_exception:
            raise type(last_exception)(error_msg) from last_exception
        else:
            raise RuntimeError(error_msg)

    def get_model_name(self) -> str:
        """Get the current active model identifier."""
        return self.current_provider.get_model_name()

    @property
    def provider_name(self) -> str:
        """Get the current active provider name."""
        return self.current_provider.provider_name

    def get_provider_status(self) -> dict[str, Any]:
        """Get status of all providers in the chain.

        Returns:
            Dictionary with provider statuses
        """
        return {
            "current_provider": self.current_provider.provider_name,
            "current_model": self.current_provider.get_model_name(),
            "available_providers": [
                {
                    "name": p.provider_name,
                    "model": p.get_model_name(),
                    "exhausted": idx in self._exhausted_providers,
                }
                for idx, p in enumerate(self.providers)
            ],
            "exhausted_count": len(self._exhausted_providers),
            "remaining_count": len(self.providers) - len(self._exhausted_providers),
        }
