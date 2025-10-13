#!/usr/bin/env python3
"""Demo script showing LLM provider fallback in action.

This script demonstrates how the fallback system automatically switches
between providers when quota/credit errors occur.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from curator.llm import LLMMessage, create_llm_provider, create_llm_provider_from_config


def demo_basic_usage():
    """Demo 1: Basic fallback configuration."""
    print("=" * 70)
    print("Demo 1: Basic Fallback Usage")
    print("=" * 70)

    # Create provider with fallback chain
    print("\n📋 Creating provider with fallback chain:")
    print("   Primary: anthropic")
    print("   Fallback #1: openai")
    print("   Fallback #2: ollama")
    print()

    try:
        provider = create_llm_provider(
            provider="anthropic", fallback_providers=["openai", "ollama"]
        )

        print(f"✅ Provider created: {provider.__class__.__name__}")

        # Check if it's a fallback provider
        from curator.llm.fallback_provider import FallbackLLMProvider

        if isinstance(provider, FallbackLLMProvider):
            status = provider.get_provider_status()
            print(f"   Current provider: {status['current_provider']}")
            print(f"   Total providers in chain: {len(status['available_providers'])}")
            print()
            print("   Provider chain:")
            for p in status["available_providers"]:
                print(f"     - {p['name']} ({p['model']})")
    except Exception as e:
        print(f"❌ Error: {e}")

    print()


def demo_config_file():
    """Demo 2: Load from config file."""
    print("=" * 70)
    print("Demo 2: Loading from Config File")
    print("=" * 70)

    config_path = "config/curator.yaml"

    print(f"\n📋 Loading provider from {config_path}")
    print()

    try:
        provider = create_llm_provider_from_config(config_path)

        print(f"✅ Provider loaded: {provider.__class__.__name__}")

        from curator.llm.fallback_provider import FallbackLLMProvider

        if isinstance(provider, FallbackLLMProvider):
            status = provider.get_provider_status()
            print("   Fallback enabled: Yes")
            print(f"   Current provider: {status['current_provider']}")
            print(f"   Fallback chain: {len(status['available_providers'])} providers")
        else:
            print("   Fallback enabled: No (single provider)")

    except Exception as e:
        print(f"❌ Error: {e}")

    print()


def demo_completion():
    """Demo 3: Actual completion with fallback (if credentials available)."""
    print("=" * 70)
    print("Demo 3: LLM Completion with Fallback")
    print("=" * 70)

    print("\n📋 Attempting LLM completion...")
    print("   (Will automatically fall back if primary provider fails)")
    print()

    # Check if we have any API keys
    has_anthropic = os.getenv("ANTHROPIC_API_KEY")
    has_openai = os.getenv("OPENAI_API_KEY")

    if not has_anthropic and not has_openai:
        print("⚠️  No API keys found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY to test.")
        print("   Skipping completion demo.")
        print()
        return

    try:
        # Create provider (will use available keys)
        fallback_list = []
        if has_openai:
            fallback_list.append("openai")
        fallback_list.append("ollama")  # Local fallback

        provider = create_llm_provider(
            provider="anthropic" if has_anthropic else "openai",
            fallback_providers=fallback_list if fallback_list else None,
        )

        # Try a simple completion
        messages = [
            LLMMessage(
                role="user",
                content="Say 'Hello from fallback demo!' and nothing else.",
            )
        ]

        print("🔄 Sending request to LLM...")
        response = provider.complete(messages, max_tokens=100)

        print(f"✅ Response received from: {response.model}")
        print(f"   Content: {response.content.strip()}")

        if response.usage:
            print(f"   Tokens: {response.usage.get('total_tokens', 'N/A')}")

    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")

    print()


def demo_simulated_failure():
    """Demo 4: Simulate provider failure."""
    print("=" * 70)
    print("Demo 4: Simulated Provider Failure")
    print("=" * 70)

    print("\n📋 This would show automatic failover in case of:")
    print("   • Credit balance exhaustion")
    print("   • Rate limit errors")
    print("   • API unavailability")
    print()
    print("   When such errors occur, the system automatically:")
    print("   1. Catches the error")
    print("   2. Marks the provider as exhausted")
    print("   3. Tries the next provider in the chain")
    print("   4. Logs the failover for visibility")
    print()
    print("   Example log output:")
    print("   ⚠️  Provider anthropic failed: Credit balance too low")
    print("   🔄 Trying next provider in chain...")
    print("   ✅ Successfully failed over to provider: openai")
    print()


def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("LLM Provider Fallback Demo")
    print("=" * 70)
    print()
    print("This demo shows how GitHub Curator automatically falls back")
    print("between LLM providers when credit balance or quota issues occur.")
    print()

    # Run demos
    demo_basic_usage()
    demo_config_file()
    demo_completion()
    demo_simulated_failure()

    print("=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print()
    print("To enable fallback in your workflow:")
    print("  1. Edit config/curator.yaml")
    print("  2. Set fallback_enabled: true")
    print("  3. Configure fallback_providers list")
    print("  4. Set environment variables for API keys")
    print()
    print("See docs/LLM_FALLBACK.md for detailed setup instructions.")
    print()


if __name__ == "__main__":
    main()
