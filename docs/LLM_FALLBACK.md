# LLM Provider Fallback

## Overview

GitHub Curator supports automatic fallback between LLM providers to ensure continuous operation even when a provider's credit balance is depleted or rate limits are hit.

## Problem Solved

When running long curation jobs, you might hit:
- **Credit/quota exhaustion**: "Your credit balance is too low to access the Anthropic API"
- **Rate limits**: Temporary throttling by the provider
- **API unavailability**: Temporary service outages

The fallback system automatically switches to backup providers, allowing your curation work to continue uninterrupted.

## Configuration

Edit `config/curator.yaml`:

```yaml
llm:
  # Primary provider
  provider: anthropic

  # Enable automatic fallback
  fallback_enabled: true

  # Fallback chain (tried in order)
  fallback_providers:
    - openai     # Try OpenAI first
    - ollama     # Then try local Ollama

  # Models for each provider
  models:
    anthropic: claude-sonnet-4-5-20250929
    openai: gpt-4o
    ollama: llama3.3

  # Provider-specific settings
  providers:
    ollama:
      base_url: http://localhost:11434
```

## How It Works

### Fallback Chain

When `fallback_enabled: true`, the system creates a fallback chain:

1. **Primary Provider**: Anthropic Claude (configured via `provider`)
2. **Fallback #1**: OpenAI GPT-4 (requires `OPENAI_API_KEY`)
3. **Fallback #2**: Local Ollama (requires Ollama running locally)

### Error Detection

The system automatically fails over when detecting:
- Credit/quota exceeded
- Rate limit errors
- API unavailability

### Transparent Failover

```
🔬 Collecting repositories...
ℹ️  Attempting LLM completion with provider: anthropic (model: claude-sonnet-4-5-20250929)
⚠️  Provider anthropic failed: Credit balance too low. Trying next provider...
ℹ️  Attempting LLM completion with provider: openai (model: gpt-4o)
✅ Successfully failed over to provider: openai
```

## Setup Guide

### 1. Anthropic Claude (Primary)

```bash
export ANTHROPIC_API_KEY=your_key_here
```

### 2. OpenAI (Fallback #1)

Install dependencies:
```bash
pip install langchain-openai openai
```

Set API key:
```bash
export OPENAI_API_KEY=your_key_here
```

### 3. Ollama (Fallback #2 - Local)

Install Ollama:
```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Or download from https://ollama.com
```

Pull a model:
```bash
ollama pull llama3.3
# or
ollama pull gemma2
```

Start Ollama server:
```bash
ollama serve
# Runs on http://localhost:11434
```

## Recommended Configurations

### Development (Cost-conscious)

```yaml
llm:
  provider: anthropic
  fallback_enabled: true
  fallback_providers:
    - ollama  # Free local alternative
```

### Production (High availability)

```yaml
llm:
  provider: anthropic
  fallback_enabled: true
  fallback_providers:
    - openai   # Commercial backup
    - ollama   # Local fallback
```

### Testing (Local only)

```yaml
llm:
  provider: ollama
  fallback_enabled: false  # No fallback needed
```

## Programmatic Usage

### Using Config File

```python
from curator.llm import create_llm_provider_from_config

# Automatically loads config with fallback chain
provider = create_llm_provider_from_config("config/curator.yaml")

# Use normally - fallback is automatic
from curator.llm import LLMMessage
response = provider.complete([
    LLMMessage(role="user", content="Evaluate this repository...")
])
```

### Manual Fallback Chain

```python
from curator.llm import create_llm_provider

# Create with fallback chain
provider = create_llm_provider(
    provider="anthropic",
    fallback_providers=["openai", "ollama"]
)
```

### Check Provider Status

```python
from curator.llm.fallback_provider import FallbackLLMProvider

if isinstance(provider, FallbackLLMProvider):
    status = provider.get_provider_status()
    print(f"Current provider: {status['current_provider']}")
    print(f"Exhausted providers: {status['exhausted_count']}")
    print(f"Remaining providers: {status['remaining_count']}")
```

## Error Classes

The system distinguishes between different error types:

- **`LLMQuotaExceededError`**: Credit balance or quota exhausted
- **`LLMRateLimitError`**: Temporary rate limiting
- **`LLMAuthenticationError`**: Invalid API key
- **`LLMAPIError`**: General API errors

Fallback triggers only for quota and rate limit errors by default.

## Best Practices

### 1. Always Configure Fallback

Enable fallback in production to avoid interruptions:
```yaml
fallback_enabled: true
```

### 2. Test Your Fallback Chain

Before long runs, verify all providers work:
```bash
# Test Anthropic
export ANTHROPIC_API_KEY=...
python -c "from curator.llm import create_llm_provider; create_llm_provider('anthropic')"

# Test OpenAI
export OPENAI_API_KEY=...
python -c "from curator.llm import create_llm_provider; create_llm_provider('openai')"

# Test Ollama
ollama serve &
python -c "from curator.llm import create_llm_provider; create_llm_provider('ollama')"
```

### 3. Monitor Provider Usage

Check logs to see which providers are being used:
```bash
curator research collect my-research --verbose
```

### 4. Ollama as Safety Net

Always include Ollama as final fallback - it's free and runs locally:
```yaml
fallback_providers:
  - openai
  - ollama
```

## Troubleshooting

### "No providers available"

Install missing dependencies:
```bash
pip install langchain-openai langchain-ollama openai
```

### "Ollama connection refused"

Start Ollama server:
```bash
ollama serve
```

### "All providers exhausted"

All providers failed. Check:
1. API keys are set correctly
2. API credits are available for all providers
3. Ollama is running (if configured)
4. Network connectivity

### Fallback not triggering

Verify fallback is enabled:
```yaml
fallback_enabled: true  # Not false
```

## Performance Considerations

### Cost

- **Anthropic Claude**: ~$3-15 per million input tokens
- **OpenAI GPT-4**: ~$2.50-30 per million input tokens
- **Ollama (local)**: Free, but uses local compute

### Speed

- **Claude/GPT-4**: 1-3 seconds per request
- **Ollama**: 3-10 seconds (depends on hardware)

### Quality

- **Claude Sonnet 4.5**: Best for code analysis
- **GPT-4**: Excellent alternative
- **Llama 3.3**: Good for most tasks, may need more guidance

## Migration Guide

### From Direct Anthropic Client

**Before:**
```python
import anthropic
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
```

**After:**
```python
from curator.llm import create_llm_provider_from_config
provider = create_llm_provider_from_config()
```

Benefits:
- Automatic fallback
- Provider abstraction
- Consistent interface

## See Also

- [LLM Providers Documentation](LLM_PROVIDERS.md)
- [Configuration Reference](../config/curator.yaml)
- [Cost Tracking](features/cost-tracking.md)
