# LLM Provider Configuration

GitHub Curator supports multiple LLM providers through a unified interface powered by LangChain. You can use Anthropic Claude, OpenAI, Google Gemini, or local models via Ollama.

## Quick Start

### Default (Anthropic Claude)

By default, the curator uses Anthropic's Claude:

```bash
export ANTHROPIC_API_KEY="your-api-key"
curator curate "AI agents with tool use"
```

### Using OpenAI

```bash
# Install OpenAI support
pip install github-curator[openai]

# Set environment variables
export CURATOR_LLM_PROVIDER=openai
export OPENAI_API_KEY="your-api-key"

# Run curator
curator curate "AI agents with tool use"
```

### Using Google Gemini

```bash
# Install Google support
pip install github-curator[google]

# Set environment variables
export CURATOR_LLM_PROVIDER=google
export GOOGLE_API_KEY="your-api-key"

# Run curator
curator curate "AI agents with tool use"
```

### Using Ollama (Local Models)

```bash
# Install Ollama support
pip install github-curator[ollama]

# Make sure Ollama is running locally
# Visit https://ollama.com for installation instructions

# Pull a model (e.g., llama3.3)
ollama pull llama3.3

# Set environment variable
export CURATOR_LLM_PROVIDER=ollama

# Run curator
curator curate "AI agents with tool use"
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CURATOR_LLM_PROVIDER` | Provider name (anthropic, openai, google, ollama) | `anthropic` |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `GOOGLE_API_KEY` | Google API key | - |

### Configuration File

Edit `config/curator.yaml` to customize provider settings:

```yaml
llm:
  # Default provider
  provider: anthropic

  # Use LangChain (recommended)
  use_langchain: true

  # Model per provider
  models:
    anthropic: claude-sonnet-4-5-20250929
    openai: gpt-4o
    google: gemini-2.0-flash-exp
    ollama: llama3.3

  # Provider-specific settings
  providers:
    ollama:
      base_url: http://localhost:11434

  # Fallback configuration
  fallback_enabled: false
  fallback_providers:
    - openai
    - google
```

## Programmatic Usage

### Basic Usage

```python
from curator.llm import create_llm_provider, LLMMessage

# Use default provider (Anthropic)
provider = create_llm_provider()

# Use specific provider
provider = create_llm_provider(provider="openai", model="gpt-4o")

# Generate completion
messages = [
    LLMMessage(role="user", content="Explain AI agents")
]
response = provider.complete(messages, max_tokens=1000)
print(response.content)
```

### Advanced Configuration

```python
from curator.llm import create_llm_provider

# Custom OpenAI endpoint
provider = create_llm_provider(
    provider="openai",
    model="gpt-4o",
    base_url="https://custom-endpoint.com/v1"
)

# Local Ollama with custom URL
provider = create_llm_provider(
    provider="ollama",
    model="llama3.3",
    base_url="http://192.168.1.100:11434"
)

# Anthropic with custom parameters
provider = create_llm_provider(
    provider="anthropic",
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    temperature=0.7
)
```

### Provider Fallback

```python
from curator.llm import create_llm_provider
from curator.errors import LLMError

providers = ["anthropic", "openai", "google"]

for provider_name in providers:
    try:
        provider = create_llm_provider(provider=provider_name)
        response = provider.complete(messages)
        print(f"Success with {provider_name}")
        break
    except LLMError as e:
        print(f"Failed with {provider_name}: {e}")
        continue
```

## Provider Comparison

| Provider | Pros | Cons | Best For |
|----------|------|------|----------|
| **Anthropic Claude** | - Excellent instruction following<br>- Long context (200K)<br>- Strong reasoning | - API only<br>- Requires API key | Production deployments |
| **OpenAI** | - Well-documented<br>- Fast inference<br>- Good ecosystem | - API only<br>- Cost can add up | General purpose |
| **Google Gemini** | - Competitive pricing<br>- Multimodal support<br>- Fast | - Newer, less tested<br>- API only | Cost-sensitive use cases |
| **Ollama** | - Free (local)<br>- Privacy<br>- No rate limits | - Requires local GPU<br>- Slower<br>- Lower quality | Development, privacy-critical |

## Model Recommendations

### For Production Curation

- **Anthropic**: `claude-sonnet-4-5-20250929` (best balance)
- **OpenAI**: `gpt-4o` (most reliable)
- **Google**: `gemini-2.0-flash-exp` (fast + cheap)

### For Development/Testing

- **Anthropic**: `claude-3-5-haiku-20241022` (cheaper)
- **OpenAI**: `gpt-4o-mini` (cheaper)
- **Google**: `gemini-2.0-flash-exp` (cheap)
- **Ollama**: `llama3.3` (free, local)

### For High-Volume Processing

- **Google**: `gemini-2.0-flash-exp` (best cost/performance)
- **Ollama**: `llama3.3` (if you have GPU)

## Error Handling

The curator provides detailed error messages for common issues:

### Authentication Errors

```python
from curator.errors import LLMAuthenticationError

try:
    provider = create_llm_provider(provider="openai")
except LLMAuthenticationError as e:
    print(f"Auth failed: {e}")
    print(f"Solution: {e.details['solution']}")
```

### Rate Limit Errors

```python
from curator.errors import LLMRateLimitError
import time

try:
    response = provider.complete(messages)
except LLMRateLimitError as e:
    print(f"Rate limited. Retry after: {e.details.get('retry_after')}")
    time.sleep(60)  # Wait and retry
```

### Model Errors

```python
from curator.errors import LLMModelError

try:
    provider = create_llm_provider(provider="openai", model="gpt-999")
except LLMModelError as e:
    print(f"Model error: {e}")
    print(f"Provider: {e.details['provider']}")
    print(f"Model: {e.details['model']}")
```

## Installation Options

### Minimal (Anthropic only)

```bash
pip install github-curator
```

### With OpenAI

```bash
pip install github-curator[openai]
```

### With All Providers

```bash
pip install github-curator[all-providers]
```

### Custom Installation

```bash
# Anthropic + OpenAI only
pip install github-curator[openai]

# Anthropic + Google only
pip install github-curator[google]

# Anthropic + Ollama only
pip install github-curator[ollama]
```

## Troubleshooting

### "Module not found" errors

If you get import errors, install the required provider:

```bash
# For OpenAI
pip install langchain-openai openai

# For Google
pip install langchain-google-genai google-generativeai

# For Ollama
pip install langchain-ollama
```

### Ollama connection issues

Make sure Ollama is running:

```bash
# Check if Ollama is running
curl http://localhost:11434/api/version

# Start Ollama if needed (depends on installation method)
ollama serve
```

### API key not found

Set environment variables in your shell or `.env` file:

```bash
# In terminal
export ANTHROPIC_API_KEY="sk-ant-..."

# Or in .env file
echo 'ANTHROPIC_API_KEY=sk-ant-...' >> .env
```

## Performance Tips

1. **Use caching**: The curator automatically caches GitHub API results
2. **Choose faster models**: Use `gemini-2.0-flash-exp` or `gpt-4o-mini` for development
3. **Local models**: Use Ollama for unlimited requests (if you have GPU)
4. **Batch processing**: Process multiple repos in parallel (built-in via Prefect)

## Security Notes

1. **Never commit API keys** to version control
2. **Use environment variables** for API keys
3. **Rotate keys regularly** for production use
4. **Use Ollama** for sensitive data that shouldn't leave your network
5. **Monitor costs** when using cloud providers

## Next Steps

- [Configuration Guide](../QUICKSTART.md)
- [Error Handling](errors.md)
- [Advanced Usage](../docs/USAGE.md)
