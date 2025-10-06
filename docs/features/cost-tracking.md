# Feature: Cost Awareness & Tracking

**Status**: 📋 Planned
**Priority**: P1
**Estimated Effort**: 1-2 days

## Overview

Add cost tracking to show users how much of their API budget was consumed by each command (`curate`, `mark`, `collect`). This helps users:
- Monitor spending in real-time
- Choose cost-effective providers/models
- Optimize their usage patterns
- Avoid surprise bills

## Requirements

### Phase 1: Basic Cost Display (Current Plan)
- Track token usage per command execution
- Calculate estimated cost based on provider pricing
- Display cost summary after command completion
- Support all providers (Anthropic, OpenAI, Google, Ollama)

### Phase 2: Advanced Features (Future)
- Cost budgets and alerts
- Historical cost tracking
- Cost breakdown by operation (intent structuring, evaluation, etc.)
- Export cost reports

## Design

### 1. Cost Calculator Module

```python
# curator/cost/calculator.py

from dataclasses import dataclass
from typing import Optional

@dataclass
class ProviderPricing:
    """Pricing information for an LLM provider."""
    provider: str
    model: str
    input_price_per_1m: float  # USD per 1M input tokens
    output_price_per_1m: float  # USD per 1M output tokens

    def calculate(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD."""
        input_cost = (input_tokens / 1_000_000) * self.input_price_per_1m
        output_cost = (output_tokens / 1_000_000) * self.output_price_per_1m
        return input_cost + output_cost

# Pricing as of Oct 2025 (needs regular updates)
PROVIDER_PRICING = {
    "anthropic": {
        "claude-sonnet-4-5-20250929": ProviderPricing(
            provider="anthropic",
            model="claude-sonnet-4-5-20250929",
            input_price_per_1m=3.0,
            output_price_per_1m=15.0,
        ),
        "claude-3-5-haiku-20241022": ProviderPricing(
            provider="anthropic",
            model="claude-3-5-haiku-20241022",
            input_price_per_1m=0.80,
            output_price_per_1m=4.0,
        ),
    },
    "openai": {
        "gpt-4o": ProviderPricing(
            provider="openai",
            model="gpt-4o",
            input_price_per_1m=2.50,
            output_price_per_1m=10.0,
        ),
        "gpt-4o-mini": ProviderPricing(
            provider="openai",
            model="gpt-4o-mini",
            input_price_per_1m=0.15,
            output_price_per_1m=0.60,
        ),
    },
    "google": {
        "gemini-2.0-flash-exp": ProviderPricing(
            provider="google",
            model="gemini-2.0-flash-exp",
            input_price_per_1m=0.10,
            output_price_per_1m=0.40,
        ),
    },
    "ollama": {
        # Ollama is free (local)
        "default": ProviderPricing(
            provider="ollama",
            model="default",
            input_price_per_1m=0.0,
            output_price_per_1m=0.0,
        ),
    },
}

def get_pricing(provider: str, model: str) -> Optional[ProviderPricing]:
    """Get pricing for a provider/model combination."""
    provider_models = PROVIDER_PRICING.get(provider, {})
    return provider_models.get(model)

class CostTracker:
    """Track costs across multiple API calls."""

    def __init__(self):
        self.calls: list[dict] = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0

    def add_call(self, provider: str, model: str, input_tokens: int, output_tokens: int):
        """Record an API call."""
        pricing = get_pricing(provider, model)
        cost = 0.0

        if pricing:
            cost = pricing.calculate(input_tokens, output_tokens)

        self.calls.append({
            "provider": provider,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost,
        })

        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost += cost

    def get_summary(self) -> dict:
        """Get cost summary."""
        return {
            "total_calls": len(self.calls),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost_usd": self.total_cost,
            "calls": self.calls,
        }
```

### 2. Integration with LLM Providers

Update `BaseLLMProvider.complete()` to accept an optional `CostTracker`:

```python
# curator/llm/base.py

def complete(
    self,
    messages: list[LLMMessage],
    max_tokens: int = 2000,
    temperature: float = 1.0,
    cost_tracker: Optional["CostTracker"] = None,
    **kwargs: Any,
) -> LLMResponse:
    """Generate completion (to be implemented by subclasses)."""
    # After getting response...
    if cost_tracker:
        cost_tracker.add_call(
            provider=self.provider_name,
            model=self.get_model_name(),
            input_tokens=response.usage.get("input_tokens", 0),
            output_tokens=response.usage.get("output_tokens", 0),
        )
    return response
```

### 3. CLI Display

After each command, show a cost summary:

```
✓ Curation complete!

📊 API Usage:
   Requests: 15
   Input tokens: 45,231
   Output tokens: 12,405
   Total tokens: 57,636

💰 Estimated cost: $0.87 USD
   (using claude-sonnet-4-5-20250929 @ $3/$15 per 1M tokens)

💡 Tip: Use 'gpt-4o-mini' to reduce costs by ~90%
```

### 4. Command Updates

Update all commands to use `CostTracker`:

```python
# curator/__main__.py

@cli.command()
def curate(...):
    from curator.cost.calculator import CostTracker

    cost_tracker = CostTracker()

    # Pass cost_tracker to all LLM calls
    provider = create_llm_provider()
    # ... use provider with cost_tracker

    # At the end
    _display_cost_summary(cost_tracker)

def _display_cost_summary(tracker: CostTracker):
    """Display cost summary."""
    summary = tracker.get_summary()

    if summary["total_calls"] == 0:
        return

    click.echo("")
    click.echo("📊 API Usage:")
    click.echo(f"   Requests: {summary['total_calls']}")
    click.echo(f"   Input tokens: {summary['total_input_tokens']:,}")
    click.echo(f"   Output tokens: {summary['total_output_tokens']:,}")
    click.echo(f"   Total tokens: {summary['total_tokens']:,}")

    if summary["total_cost_usd"] > 0:
        click.echo("")
        click.echo(f"💰 Estimated cost: ${summary['total_cost_usd']:.4f} USD")

        # Show tip for expensive providers
        if summary["total_cost_usd"] > 0.10:
            click.echo("")
            click.echo("💡 Tip: Consider using cheaper models:")
            click.echo("   - gpt-4o-mini (OpenAI) - ~90% cheaper")
            click.echo("   - gemini-2.0-flash-exp (Google) - ~95% cheaper")
            click.echo("   - llama3.3 (Ollama) - Free!")
    else:
        click.echo("")
        click.echo("💰 Cost: FREE (using local model)")
```

## Implementation Plan

### Step 1: Create Cost Calculator Module
- [ ] Create `curator/cost/__init__.py`
- [ ] Create `curator/cost/calculator.py` with pricing data
- [ ] Add `CostTracker` class
- [ ] Add pricing update mechanism (for future maintenance)

### Step 2: Update LLM Providers
- [ ] Update `BaseLLMProvider` interface to accept `cost_tracker`
- [ ] Update all provider implementations (Anthropic, OpenAI, etc.)
- [ ] Ensure token counts are correctly extracted from responses

### Step 3: Update CLI Commands
- [ ] Add `_display_cost_summary()` helper function
- [ ] Update `curate` command to use `CostTracker`
- [ ] Update `mark` command to use `CostTracker`
- [ ] Update `collect` command to use `CostTracker`

### Step 4: Testing
- [ ] Test with Anthropic Claude
- [ ] Test with OpenAI
- [ ] Test with Google Gemini
- [ ] Test with Ollama (should show $0)
- [ ] Verify token counts are accurate

### Step 5: Documentation
- [ ] Update [LLM_PROVIDERS.md](../LLM_PROVIDERS.md) with cost information
- [ ] Add cost comparison table
- [ ] Add tips for cost optimization
- [ ] Update [QUICKSTART.md](../../QUICKSTART.md) with cost examples

## Example Output

```bash
$ curator curate "AI agents with tool use"
🔍 Structuring intent...
🔎 Searching GitHub...
📊 Evaluating 25 repositories...
✅ Curation complete!

📊 API Usage:
   Requests: 28
   Input tokens: 125,430
   Output tokens: 34,221
   Total tokens: 159,651

💰 Estimated cost: $1.89 USD
   Provider: anthropic (claude-sonnet-4-5-20250929)
   Pricing: $3.00 / $15.00 per 1M tokens

💡 Cost savings opportunities:
   - Switch to gpt-4o-mini: ~$0.17 (-91%)
   - Switch to gemini-2.0-flash-exp: ~$0.15 (-92%)
   - Use Ollama locally: $0.00 (FREE)

📝 Report saved to: output/reports/curated_list_abc123.md
```

## Cost Comparison

| Provider | Model | Input ($/1M) | Output ($/1M) | Example Cost* |
|----------|-------|--------------|---------------|---------------|
| Anthropic | Claude Sonnet 4.5 | $3.00 | $15.00 | $1.89 |
| Anthropic | Claude 3.5 Haiku | $0.80 | $4.00 | $0.52 |
| OpenAI | GPT-4o | $2.50 | $10.00 | $1.66 |
| OpenAI | GPT-4o-mini | $0.15 | $0.60 | $0.17 |
| Google | Gemini 2.0 Flash | $0.10 | $0.40 | $0.15 |
| Ollama | Llama 3.3 | $0.00 | $0.00 | **FREE** |

*Example: 125K input + 34K output tokens (typical for curating 25 repos)

## Configuration

Add cost display preferences to `curator.yaml`:

```yaml
cost:
  display_summary: true
  display_breakdown: false  # detailed per-call breakdown
  show_tips: true          # show cost optimization tips
  currency: USD

  # Future: cost alerts
  alerts:
    warn_at: 1.00  # USD
    max_cost: 10.00  # USD
```

## Future Enhancements (Phase 2)

1. **Cost Budgets**
   - Set daily/monthly budgets
   - Alert when approaching limit
   - Auto-stop when exceeded

2. **Historical Tracking**
   - Store cost data in `.curator/costs.jsonl`
   - Generate monthly reports
   - Track cost trends

3. **Cost Breakdown**
   - Per-operation costs (intent, evaluation, reflection)
   - Per-repository costs
   - Cost vs. quality analysis

4. **Smart Cost Optimization**
   - Auto-suggest cheaper models
   - Batch operations to reduce costs
   - Cache expensive operations

5. **Export & Reporting**
   - CSV export for accounting
   - Cost reports by project
   - Integration with billing systems

## References

- [Anthropic Pricing](https://www.anthropic.com/pricing)
- [OpenAI Pricing](https://openai.com/pricing)
- [Google AI Pricing](https://ai.google.dev/pricing)
- [Ollama](https://ollama.com) - Free & open source

## Success Metrics

- ✅ Users can see cost after every command
- ✅ Cost calculations are accurate (±5%)
- ✅ All providers supported
- ✅ Documentation includes cost guidance
- ✅ Users report making informed decisions about provider choice

---

**Next Steps**: Implement Phase 1 (basic cost display) in Week 2 alongside semantic search features.
