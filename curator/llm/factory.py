"""LLM provider factory for creating provider instances."""

import logging
import os
from typing import Any, Optional

from curator.llm.base import BaseLLMProvider

logger = logging.getLogger(__name__)


def create_llm_provider(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    use_langchain: bool = True,
    fallback_providers: Optional[list[str]] = None,
    **kwargs: Any,
) -> BaseLLMProvider:
    """Create an LLM provider instance with optional fallback chain.

    Args:
        provider: Provider name (anthropic, openai, google, ollama)
                 Defaults to CURATOR_LLM_PROVIDER env var or "anthropic"
        model: Model identifier (uses provider defaults if not specified)
        api_key: API key (uses environment variables if not specified)
        use_langchain: Whether to use LangChain-based provider (recommended)
        fallback_providers: List of provider names to try if primary fails
                           (e.g., ["openai", "ollama"])
        **kwargs: Additional provider-specific arguments

    Returns:
        BaseLLMProvider instance (FallbackLLMProvider if fallbacks specified)

    Examples:
        # Use default (Anthropic with LangChain)
        provider = create_llm_provider()

        # Use OpenAI with fallback to Ollama
        provider = create_llm_provider(
            provider="openai",
            fallback_providers=["ollama"]
        )

        # Full fallback chain: Anthropic -> OpenAI -> Ollama
        provider = create_llm_provider(
            provider="anthropic",
            fallback_providers=["openai", "ollama"]
        )

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

    # Extract internal config keys for fallback providers (don't pass to primary)
    models_config = kwargs.pop("_models_config", {})
    providers_config = kwargs.pop("_providers_config", {})

    # Create primary provider
    primary_provider: BaseLLMProvider
    if use_langchain:
        # Use unified LangChain provider (recommended)
        from curator.llm.langchain_provider import LangChainProvider

        primary_provider = LangChainProvider(
            provider=provider_name,
            model=model,
            api_key=api_key,
            **kwargs,
        )
    else:
        # Use legacy direct providers
        if provider_name == "anthropic":
            from curator.llm.anthropic_provider import AnthropicProvider

            primary_provider = AnthropicProvider(
                api_key=api_key,
                model=model or "claude-sonnet-4-5-20250929",
            )
        elif provider_name == "openai":
            from curator.llm.openai_provider import OpenAIProvider

            primary_provider = OpenAIProvider(
                api_key=api_key,
                model=model or "gpt-4o",
                base_url=kwargs.get("base_url"),
            )
        else:
            raise ValueError(
                f"Unsupported provider: {provider_name}. "
                f"Supported providers (legacy): anthropic, openai"
            )

    # If no fallback providers, return primary
    if not fallback_providers:
        return primary_provider

    # Create fallback chain
    logger.info(f"Creating fallback chain: {provider_name} -> {', '.join(fallback_providers)}")

    from curator.llm.fallback_provider import FallbackLLMProvider

    # Build provider chain: primary + fallbacks
    provider_chain: list[BaseLLMProvider] = [primary_provider]

    for fallback_name in fallback_providers:
        try:
            # Get model and settings for this fallback provider
            fallback_model = models_config.get(fallback_name)
            fallback_settings = providers_config.get(fallback_name, {}).copy()

            # Create fallback provider (recursively, but without further fallbacks)
            fallback = create_llm_provider(
                provider=fallback_name,
                model=fallback_model,
                use_langchain=use_langchain,
                fallback_providers=None,  # No nested fallbacks
                **fallback_settings,
            )
            provider_chain.append(fallback)
            logger.debug(f"Added fallback provider: {fallback_name}")
        except Exception as e:
            logger.warning(f"Failed to create fallback provider {fallback_name}: {e}. Skipping.")
            continue

    if len(provider_chain) == 1:
        logger.warning("No fallback providers could be created, using primary only")
        return primary_provider

    return FallbackLLMProvider(providers=provider_chain)


def create_llm_provider_from_config(
    config_path: str = "config/curator.yaml",
) -> BaseLLMProvider:
    """Create LLM provider from configuration file with fallback support.

    Reads the curator.yaml configuration and creates a provider with optional
    fallback chain based on the config settings.

    Args:
        config_path: Path to curator.yaml configuration file

    Returns:
        BaseLLMProvider instance (possibly FallbackLLMProvider)

    Example config.yaml:
        llm:
          provider: anthropic
          use_langchain: true
          fallback_enabled: true
          fallback_providers:
            - openai
            - ollama

          models:
            anthropic: claude-sonnet-4-5-20250929
            openai: gpt-4o
            ollama: llama3.3

          providers:
            ollama:
              base_url: http://localhost:11434
    """
    import yaml

    # Load config
    with open(config_path) as f:
        config = yaml.safe_load(f)

    llm_config = config.get("llm", {})

    # Extract settings
    provider = llm_config.get("provider", "anthropic")
    use_langchain = llm_config.get("use_langchain", True)
    fallback_enabled = llm_config.get("fallback_enabled", False)
    fallback_providers_list = llm_config.get("fallback_providers", [])

    # Get model mapping
    models = llm_config.get("models", {})
    model = models.get(provider)

    # Get provider-specific settings
    providers_config = llm_config.get("providers", {})
    provider_settings = providers_config.get(provider, {})

    # Build kwargs
    kwargs = provider_settings.copy()

    # If fallback enabled, pass models and providers_config for fallback providers
    if fallback_enabled and fallback_providers_list:
        kwargs["_models_config"] = models
        kwargs["_providers_config"] = providers_config

    # Create provider with optional fallbacks
    return create_llm_provider(
        provider=provider,
        model=model,
        use_langchain=use_langchain,
        fallback_providers=fallback_providers_list if fallback_enabled else None,
        **kwargs,
    )


def get_available_providers() -> list[str]:
    """Get list of available LLM providers.

    Returns:
        List of provider names that can be used
    """
    providers = ["anthropic"]  # Always available (in dependencies)

    # Check for optional providers
    try:
        import langchain_openai  # type: ignore[import-not-found] # noqa: F401

        providers.append("openai")
    except ImportError:
        pass

    try:
        import langchain_google_genai  # type: ignore[import-not-found] # noqa: F401

        providers.append("google")
    except ImportError:
        pass

    try:
        import langchain_ollama  # type: ignore[import-not-found] # noqa: F401

        providers.append("ollama")
    except ImportError:
        pass

    return providers
