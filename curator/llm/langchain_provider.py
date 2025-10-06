"""LangChain-based LLM provider for unified multi-provider support."""

import os
from typing import Any, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from curator.errors import (
    LLMAPIError,
    LLMAuthenticationError,
    LLMModelError,
    LLMRateLimitError,
)
from curator.llm.base import BaseLLMProvider, LLMMessage, LLMResponse


class LangChainProvider(BaseLLMProvider):
    """Unified LLM provider using LangChain abstractions.

    Supports multiple providers through LangChain's unified interface:
    - Anthropic Claude (langchain-anthropic)
    - OpenAI (langchain-openai)
    - Google Gemini (langchain-google-genai)
    - Ollama (langchain-ollama)
    """

    def __init__(
        self,
        provider: str = "anthropic",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs: Any,
    ):
        """Initialize LangChain provider.

        Args:
            provider: Provider name (anthropic, openai, google, ollama)
            model: Model identifier (uses provider defaults if not specified)
            api_key: API key (uses environment variables if not specified)
            base_url: Base URL for API (for Ollama or custom endpoints)
            **kwargs: Additional provider-specific arguments
        """
        self.provider = provider.lower()
        self._model = model
        self.api_key = api_key
        self.base_url = base_url
        self.kwargs = kwargs

        # Initialize the appropriate LangChain model
        self.llm = self._create_llm()

    def _create_llm(self) -> Any:
        """Create LangChain LLM instance based on provider."""
        if self.provider == "anthropic":
            return self._create_anthropic()
        elif self.provider == "openai":
            return self._create_openai()
        elif self.provider == "google":
            return self._create_google()
        elif self.provider == "ollama":
            return self._create_ollama()
        else:
            raise ValueError(
                f"Unsupported provider: {self.provider}. "
                f"Supported providers: anthropic, openai, google, ollama"
            )

    def _create_anthropic(self) -> Any:
        """Create Anthropic Claude LLM."""
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError as e:
            raise ImportError(
                "Anthropic provider requires langchain-anthropic. "
                "Install it with: pip install langchain-anthropic"
            ) from e

        api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise LLMAuthenticationError(
                provider="anthropic",
                message="Anthropic API key required",
                details={"solution": "Set ANTHROPIC_API_KEY environment variable"},
            )

        model = self._model or "claude-sonnet-4-5-20250929"

        return ChatAnthropic(
            api_key=api_key,
            model=model,
            **self.kwargs,
        )

    def _create_openai(self) -> Any:
        """Create OpenAI LLM."""
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as e:
            raise ImportError(
                "OpenAI provider requires langchain-openai. "
                "Install it with: pip install langchain-openai openai"
            ) from e

        api_key = self.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise LLMAuthenticationError(
                provider="openai",
                message="OpenAI API key required",
                details={"solution": "Set OPENAI_API_KEY environment variable"},
            )

        model = self._model or "gpt-4o"

        kwargs = self.kwargs.copy()
        if self.base_url:
            kwargs["base_url"] = self.base_url

        return ChatOpenAI(
            api_key=api_key,
            model=model,
            **kwargs,
        )

    def _create_google(self) -> Any:
        """Create Google Gemini LLM."""
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError as e:
            raise ImportError(
                "Google provider requires langchain-google-genai. "
                "Install it with: pip install langchain-google-genai google-generativeai"
            ) from e

        api_key = self.api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise LLMAuthenticationError(
                provider="google",
                message="Google API key required",
                details={"solution": "Set GOOGLE_API_KEY environment variable"},
            )

        model = self._model or "gemini-2.0-flash-exp"

        return ChatGoogleGenerativeAI(
            api_key=api_key,
            model=model,
            **self.kwargs,
        )

    def _create_ollama(self) -> Any:
        """Create Ollama LLM."""
        try:
            from langchain_ollama import ChatOllama
        except ImportError as e:
            raise ImportError(
                "Ollama provider requires langchain-ollama. "
                "Install it with: pip install langchain-ollama"
            ) from e

        model = self._model or "llama3.3"
        base_url = self.base_url or "http://localhost:11434"

        return ChatOllama(
            model=model,
            base_url=base_url,
            **self.kwargs,
        )

    def complete(
        self,
        messages: list[LLMMessage],
        max_tokens: int = 2000,
        temperature: float = 1.0,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate completion using LangChain."""
        # Convert our messages to LangChain format
        lc_messages = []
        for msg in messages:
            if msg.role == "system":
                lc_messages.append(SystemMessage(content=msg.content))
            elif msg.role == "user":
                lc_messages.append(HumanMessage(content=msg.content))
            # Note: LangChain doesn't have separate "assistant" in input,
            # it's handled via AIMessage in chat history

        try:
            # Invoke the LLM
            response = self.llm.invoke(
                lc_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs,
            )

            # Extract usage information if available
            usage = {}
            if hasattr(response, "response_metadata"):
                metadata = response.response_metadata
                if "usage" in metadata:
                    usage_data = metadata["usage"]
                    usage = {
                        "input_tokens": usage_data.get("input_tokens")
                        or usage_data.get("prompt_tokens"),
                        "output_tokens": usage_data.get("output_tokens")
                        or usage_data.get("completion_tokens"),
                        "total_tokens": usage_data.get("total_tokens"),
                    }

            return LLMResponse(
                content=response.content,
                model=self.get_model_name(),
                usage=usage,
                raw_response=response,
            )

        except Exception as e:
            # Map exceptions to our error hierarchy
            error_str = str(e).lower()

            if "auth" in error_str or "api key" in error_str or "401" in error_str:
                raise LLMAuthenticationError(
                    provider=self.provider,
                    message=f"Authentication failed: {e}",
                    details={"model": self.get_model_name()},
                ) from e

            if "rate limit" in error_str or "429" in error_str:
                raise LLMRateLimitError(
                    provider=self.provider,
                    details={"model": self.get_model_name(), "message": str(e)},
                ) from e

            if "model" in error_str or "not found" in error_str or "404" in error_str:
                raise LLMModelError(
                    provider=self.provider,
                    model=self.get_model_name(),
                    message=f"Model error: {e}",
                ) from e

            # Generic API error
            raise LLMAPIError(
                provider=self.provider,
                message=f"API error: {e}",
                details={"model": self.get_model_name()},
            ) from e

    def get_model_name(self) -> str:
        """Get model identifier."""
        if hasattr(self.llm, "model"):
            return self.llm.model
        if hasattr(self.llm, "model_name"):
            return self.llm.model_name
        return self._model or f"{self.provider}-default"

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return self.provider
