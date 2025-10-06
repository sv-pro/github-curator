"""LLM provider factory for creating provider instances."""

import os
from typing import Any, Optional

from curator.llm.base import BaseLLMProvider


def create_llm_provider(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    use_langchain: bool = True,
    **kwargs: Any,
) -> BaseLLMProvider:
    """Create an LLM provider instance.

    Args:
        provider: Provider name (anthropic, openai, google, ollama)
                 Defaults to CURATOR_LLM_PROVIDER env var or "anthropic"
        model: Model identifier (uses provider defaults if not specified)
        api_key: API key (uses environment variables if not specified)
        use_langchain: Whether to use LangChain-based provider (recommended)
        **kwargs: Additional provider-specific arguments

    Returns:
        BaseLLMProvider instance

    Examples:
        # Use default (Anthropic with LangChain)
        provider = create_llm_provider()

        # Use OpenAI
        provider = create_llm_provider(provider="openai", model="gpt-4o")

        # Use Ollama locally
        provider = create_llm_provider(
            provider="ollama",
            model="llama3.3",
            base_url="http://localhost:11434"
        )

        # Use legacy provider (without LangChain)
        provider = create_llm_provider(provider="anthropic", use_langchain=False)
    """
    # Determine provider
    provider_name = (provider or os.getenv("CURATOR_LLM_PROVIDER") or "anthropic").lower()

    if use_langchain:
        # Use unified LangChain provider (recommended)
        from curator.llm.langchain_provider import LangChainProvider

        return LangChainProvider(
            provider=provider_name,
            model=model,
            api_key=api_key,
            **kwargs,
        )
    else:
        # Use legacy direct providers
        if provider_name == "anthropic":
            from curator.llm.anthropic_provider import AnthropicProvider

            return AnthropicProvider(
                api_key=api_key,
                model=model or "claude-sonnet-4-5-20250929",
            )
        elif provider_name == "openai":
            from curator.llm.openai_provider import OpenAIProvider

            return OpenAIProvider(
                api_key=api_key,
                model=model or "gpt-4o",
                base_url=kwargs.get("base_url"),
            )
        else:
            raise ValueError(
                f"Unsupported provider: {provider_name}. "
                f"Supported providers (legacy): anthropic, openai"
            )


def get_available_providers() -> list[str]:
    """Get list of available LLM providers.

    Returns:
        List of provider names that can be used
    """
    providers = ["anthropic"]  # Always available (in dependencies)

    # Check for optional providers
    try:
        import langchain_openai  # noqa: F401

        providers.append("openai")
    except ImportError:
        pass

    try:
        import langchain_google_genai  # noqa: F401

        providers.append("google")
    except ImportError:
        pass

    try:
        import langchain_ollama  # noqa: F401

        providers.append("ollama")
    except ImportError:
        pass

    return providers
