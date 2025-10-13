# Snapshot Design Questions

## Context

After implementing the research workspace system and LLM fallback, several important design questions have emerged about how snapshots should work.

## Current State

### What Snapshots Currently Store

Snapshots are full state captures stored as JSON files:

```json
{
  "name": "baseline",
  "timestamp": "2025-10-13T18:30:45",
  "workspace": "python-async-2025",
  "theme": "python async frameworks",
  "intent": { /* structured evaluation dimensions */ },
  "evaluations": [
    {
      "repo": "owner/repo",
      "overall_relevance": 0.85,
      "confidence": 0.75,
      "dimension_scores": [ /* detailed scores */ ],
      "recommendation": "Include",
      "notes": "..."
    }
  ],
  "statistics": {
    "total_repos": 50,
    "avg_score": 0.75,
    "avg_confidence": 0.70
  }
}
```

### What diff Command Currently Does

Compares two full snapshots and calculates:
- New repos added
- Repos removed
- Score deltas for common repos
- Aggregate statistics changes

## Design Questions

### 1. Snapshot Artifacts: Full State vs Delta

**Current**: Single artifact (full state JSON)

**Question**: Should we produce TWO artifacts?

1. **Full State Snapshot** (current behavior)
   - Complete evaluation of all repos at point in time
   - Self-contained, can be used independently
   - Useful for: absolute comparisons, reporting, archival

2. **Delta Snapshot** (NEW)
   - Semantic diff since last snapshot
   - What changed and WHY
   - Useful for: understanding evolution, narrative reporting

**Proposed Structure for Delta Artifact**:
```json
{
  "name": "update-v2",
  "timestamp": "2025-10-14T10:00:00",
  "base_snapshot": "baseline",
  "workspace": "python-async-2025",
  "changes": {
    "new_repos": [
      {
        "repo": "owner/new-repo",
        "score": 0.88,
        "why_added": "Emerged as popular async testing framework",
        "key_features": ["async fixtures", "pytest plugin"]
      }
    ],
    "removed_repos": [
      {
        "repo": "owner/deprecated-repo",
        "was_score": 0.65,
        "why_removed": "No longer maintained, archived",
        "last_update": "2023-01-15"
      }
    ],
    "significant_changes": [
      {
        "repo": "owner/improved-repo",
        "old_score": 0.70,
        "new_score": 0.85,
        "delta": +0.15,
        "what_changed": "Added async context managers, improved docs",
        "dimension_changes": [
          {
            "dimension": "async_implementation",
            "old": 0.65,
            "new": 0.90,
            "why": "Implemented async context protocol"
          }
        ]
      }
    ]
  },
  "narrative_summary": "5 new repos emerged focusing on async testing. Notable improvements in async context manager support across 3 repos."
}
```

**Trade-offs**:
- Pro: Richer semantic understanding of evolution
- Pro: Better for narrative reporting ("what's new in async world")
- Con: More complex to generate (requires LLM to analyze changes)
- Con: Two files to manage per snapshot
- Con: Delta depends on having previous snapshot

**Options**:
- A: Keep only full state (current)
- B: Generate both full state + delta automatically
- C: Make delta generation optional (`--with-delta` flag)
- D: Generate delta on-demand via separate command (`curator research explain-changes`)

### 2. Git Pull Before Snapshot

**Current**: Snapshots evaluate repos as they are currently cloned

**Question**: Should `snapshot` automatically pull latest code?

**Scenario**:
```bash
# Repos were collected 2 weeks ago
curator research collect python-async-2025

# Now taking snapshot - should it pull first?
curator research snapshot python-async-2025 current
```

**Options**:

**A: Always pull before snapshot** (implicit sync)
```bash
curator research snapshot python-async-2025
# Internally: git pull all repos, then evaluate
```
- Pro: Ensures fresh evaluation
- Con: Slow (pulling 50+ repos)
- Con: User might want to evaluate specific commit
- Con: Less transparent (hidden side effect)

**B: Never pull, require explicit sync** (current)
```bash
curator research refresh python-async-2025 --sync
curator research snapshot python-async-2025
```
- Pro: Explicit control
- Pro: Can snapshot historical state
- Pro: Faster snapshots
- Con: Easy to forget to sync

**C: Add `--pull` flag to snapshot**
```bash
curator research snapshot python-async-2025 --pull
```
- Pro: Flexible
- Con: Another flag to remember

**D: Auto-pull only if repos are "stale"** (smart default)
```bash
curator research snapshot python-async-2025
# If last pull > 24 hours ago: pull first
# Otherwise: use current state
```
- Pro: Balance of fresh data and performance
- Con: Magic threshold (24h?)
- Con: Might surprise users

**E: Interactive prompt if stale**
```bash
curator research snapshot python-async-2025
⚠️  Repos last synced 3 days ago. Pull latest code? [Y/n]
```
- Pro: User awareness
- Con: Breaks automation/scripts
- Con: Annoying for frequent snapshots

### 3. LLM Provider/Model Metadata in Snapshots

**Current**: No tracking of which LLM was used

**Question**: How should we track provider/model used for each snapshot?

**Why It Matters**:
- Different models produce different evaluations
- Fallback means snapshots might use different providers
- Need reproducibility and comparability

**Proposed Metadata Structure**:

```json
{
  "name": "baseline",
  "timestamp": "2025-10-13T18:30:45",
  "llm_metadata": {
    "intent_structurer": {
      "provider": "ollama",
      "model": "llama3:latest",
      "fallback_occurred": true,
      "attempted_providers": ["anthropic", "ollama"]
    },
    "evaluations": [
      {
        "repo": "owner/repo1",
        "provider": "ollama",
        "model": "llama3:latest"
      },
      {
        "repo": "owner/repo2",
        "provider": "anthropic",
        "model": "claude-sonnet-4-5-20250929"
      }
    ]
  }
}
```

**Options**:

**A: Track at snapshot level** (aggregate)
```json
{
  "llm_metadata": {
    "primary_provider": "anthropic",
    "fallback_used": true,
    "providers_used": ["anthropic", "ollama"],
    "model_distribution": {
      "anthropic/claude-sonnet-4": 10,
      "ollama/llama3:latest": 40
    }
  }
}
```
- Pro: Simple overview
- Con: Loses per-evaluation detail

**B: Track per-evaluation** (granular)
- Pro: Complete traceability
- Pro: Can see which repos used which model
- Con: Large metadata overhead
- Con: Complex to analyze

**C: Track both levels**
- Pro: Best of both worlds
- Con: Most complex
- Con: Redundant data

**D: Track only when fallback occurs**
```json
{
  "llm_metadata": {
    "fallback_occurred": true,
    "fallback_reason": "Anthropic credit exhaustion",
    "evaluations_by_provider": {
      "anthropic": ["repo1", "repo2"],
      "ollama": ["repo3", "repo4", ...]
    }
  }
}
```
- Pro: Minimal overhead in normal case
- Con: Less useful for comparison

### 4. Snapshot Comparability

**Question**: How do we handle comparing snapshots made with different LLM providers?

**Scenario**:
```bash
# Baseline made with Anthropic
curator research snapshot python-async baseline  # Used Anthropic

# Update made with Ollama (credits exhausted)
curator research snapshot python-async update    # Used Ollama

# Compare - are scores comparable?
curator research diff python-async baseline update
```

**Challenges**:
- Different models score differently
- Score deltas might be model difference, not real change
- Confidence levels mean different things per model

**Options**:

**A: Warn on provider mismatch**
```
⚠️  Warning: Snapshots use different LLM providers
    baseline: anthropic/claude-sonnet-4
    update: ollama/llama3:latest
    Score comparisons may not be meaningful.
```

**B: Normalize scores by provider**
- Calibrate scores based on known provider biases
- Requires benchmarking different models
- Complex to implement and maintain

**C: Re-evaluate baseline with current provider**
```bash
curator research diff python-async baseline update --normalize
# Internally: re-run baseline evaluation with Ollama for fair comparison
```
- Pro: Truly comparable scores
- Con: Expensive (re-evaluation)
- Con: Loses historical provider information

**D: Accept incomparability, focus on trends**
- Document that cross-provider comparisons are approximate
- Use diff for directional insights, not absolute precision
- Provide model metadata for user judgment

## Recommendations Needed

For each question, decide:
1. Immediate solution (what to implement now)
2. Long-term vision (what's the ideal state)
3. Migration path (how to get there)

## Related Files

- Snapshot creation: [curator/__main__.py](../curator/__main__.py) lines 1628-1847
- Snapshot comparison: [curator/__main__.py](../curator/__main__.py) lines 2053-2248
- Research config: [curator/research/manager.py](../curator/research/manager.py)

## Next Steps

1. Review design questions with stakeholders
2. Choose options for each question
3. Update implementation plan
4. Document decisions in CLAUDE.md
5. Implement chosen solutions

---

**Status**: Open for discussion
**Created**: 2025-10-13
**Last Updated**: 2025-10-13
