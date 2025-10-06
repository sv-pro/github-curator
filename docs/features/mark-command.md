# Feature: Mark Command Restoration

## Overview

The `mark` command analyzes a GitHub repository and suggests relevant topics using AI-powered inference. It operates in "blind mode" by default (without looking at existing topics) to provide unbiased suggestions.

## Status

**Currently**: ⚠️ MISSING (was removed)
**Last seen**: Commit `1c91c32` (docs: Update documentation for new mark and collect commands)
**Priority**: P1 (High - core knowledge base feature)

## Original Implementation

### Command Signature
```bash
curator mark <repo> [OPTIONS]
```

### Options
- `--compare` - Show current vs suggested topics
- `--from-curation <intent_id>` - Use curation results as context
- `--knowledge-base <path>` - Path to knowledge base directory
- `--min-confidence <float>` - Minimum confidence threshold (default: 0.5)
- `--output <path>` - Save results to file
- `--format <json|yaml|text>` - Output format
- `--config <path>` - Config file path
- `--use-git-clone` - Clone repo locally for faster analysis

### Example Usage
```bash
# Blind mode: Suggest topics without seeing current ones
curator mark fastapi/fastapi

# Compare mode: Show current vs suggested
curator mark fastapi/fastapi --compare

# Use curation context
curator mark fastapi/fastapi --from-curation <intent-id>

# Filter by confidence
curator mark fastapi/fastapi --min-confidence 0.7
```

### Output Format
```json
{
  "repo": "fastapi/fastapi",
  "analyzed_at": "2025-10-06T12:00:00Z",
  "mode": "blind",
  "suggested_topics": [
    {
      "topic": "async",
      "confidence": 0.95,
      "reasoning": "Extensive async/await usage throughout codebase"
    },
    {
      "topic": "web-framework",
      "confidence": 0.92,
      "reasoning": "HTTP routing, request handling, ASGI support"
    }
  ],
  "current_topics": ["python", "fastapi", "api"],
  "comparison": {
    "new_suggestions": ["async", "web-framework"],
    "confirmed": ["python", "api"],
    "missing_from_current": ["async"]
  }
}
```

## Restoration Plan

### Step 1: Extract Original Code (30 min)
```bash
# Extract mark command from git history
git show 1c91c32:curator/__main__.py > /tmp/mark_original.py

# Extract supporting modules if any
git show 1c91c32:curator/knowledge/ --name-only
```

### Step 2: Update for Current Architecture (2 hours)

**Changes needed**:
1. Use new LangChain provider abstraction (not direct Anthropic)
2. Integrate with hybrid knowledge store
3. Use Prefect task for caching
4. Update error handling

**New implementation**:
```python
# curator/__main__.py

@cli.command()
@click.argument("repo")
@click.option("--compare", is_flag=True, help="Show current vs suggested topics")
@click.option("--from-curation", help="Use curation results as context")
@click.option("--knowledge-base", default=".curator/knowledge", help="Knowledge base path")
@click.option("--min-confidence", default=0.5, type=float, help="Minimum confidence threshold")
@click.option("--output", type=click.Path(), help="Save results to file")
@click.option("--format", type=click.Choice(["json", "yaml", "text"]), default="text")
@click.option("--use-git-clone", is_flag=True, help="Clone repo locally for analysis")
@click.option("--config", default="config/curator.yaml", help="Config file path")
def mark(repo, compare, from_curation, knowledge_base, min_confidence, output, format, use_git_clone, config):
    """Analyze repository and suggest relevant topics.

    REPO: Repository in owner/repo format (e.g., fastapi/fastapi)

    By default, operates in BLIND MODE - analyzes the repository WITHOUT
    looking at existing topics. Use --compare to see current vs suggested topics.
    """
    from curator.commands.mark import mark_repository

    try:
        result = mark_repository(
            repo=repo,
            compare_mode=compare,
            curation_id=from_curation,
            knowledge_base_path=knowledge_base,
            min_confidence=min_confidence,
            use_git_clone=use_git_clone,
            config_path=config
        )

        # Display results
        if format == "json":
            click.echo(json.dumps(result, indent=2))
        elif format == "yaml":
            click.echo(yaml.dump(result))
        else:
            display_mark_results(result, compare)

        # Save to file if requested
        if output:
            with open(output, "w") as f:
                json.dump(result, f, indent=2)
            click.echo(f"\n✅ Results saved to {output}")

    except Exception as e:
        click.echo(f"\n❌ Error analyzing repository: {e}", err=True)
        raise click.Abort()
```

### Step 3: Create Prefect Task (1 hour)
```python
# curator/pipeline/tasks.py

@task(
    name="mark-repository",
    cache_key_fn=analysis_cache_key,
    cache_expiration=timedelta(days=7),
    retries=3,
    tags=["analysis", "llm", "topics"]
)
def mark_repository_task(
    repo: str,
    compare_mode: bool = False,
    curation_id: Optional[str] = None,
    min_confidence: float = 0.5
) -> dict:
    """Analyze repository and suggest topics (Prefect task)."""
    from curator.commands.mark import analyze_topics

    return analyze_topics(
        repo=repo,
        compare_mode=compare_mode,
        curation_id=curation_id,
        min_confidence=min_confidence
    )
```

### Step 4: Integration with Hybrid Storage (1 hour)

Use vector store for topic similarity:
```python
# curator/commands/mark.py

from curator.knowledge.store import KnowledgeStore

def suggest_topics(repo_analysis, knowledge_store: KnowledgeStore):
    """Suggest topics using semantic similarity."""

    # Get repo description embedding
    repo_text = f"{repo_analysis.name}: {repo_analysis.description}"

    # Find similar topics from knowledge base
    similar_topics = knowledge_store.find_similar_topics(
        query=repo_text,
        limit=20
    )

    # Use LLM to validate and rank
    llm_response = llm.invoke([
        {"role": "system", "content": "You are analyzing repository topics."},
        {"role": "user", "content": f"""
        Repository: {repo_analysis.name}
        Description: {repo_analysis.description}
        README excerpt: {repo_analysis.readme[:500]}

        Candidate topics from similar repos:
        {[t.topic for t in similar_topics]}

        Suggest 5-10 most relevant topics with confidence scores (0-1).
        Return as JSON: {{"topics": [{{"topic": "...", "confidence": 0.9, "reasoning": "..."}}]}}
        """}
    ])

    return parse_llm_topics(llm_response)
```

### Step 5: Testing (2 hours)
```python
# tests/test_mark_command.py

def test_mark_blind_mode():
    """Test blind mode topic suggestion."""
    result = mark_repository("fastapi/fastapi", compare_mode=False)
    assert len(result["suggested_topics"]) > 0
    assert all(t["confidence"] >= 0 for t in result["suggested_topics"])

def test_mark_compare_mode():
    """Test compare mode."""
    result = mark_repository("fastapi/fastapi", compare_mode=True)
    assert "current_topics" in result
    assert "suggested_topics" in result
    assert "comparison" in result

def test_mark_min_confidence():
    """Test confidence filtering."""
    result = mark_repository("fastapi/fastapi", min_confidence=0.8)
    assert all(t["confidence"] >= 0.8 for t in result["suggested_topics"])
```

## Timeline

| Task | Duration | Dependencies |
|------|----------|--------------|
| Extract original code | 30 min | - |
| Update for LangChain | 1 hour | LLM abstraction done |
| Create Prefect task | 1 hour | Prefect pipeline Phase 1 |
| Integration with storage | 1 hour | Hybrid storage Phase 1 |
| Testing | 2 hours | All above |
| Documentation | 1 hour | All above |
| **Total** | **6.5 hours** | **~1 day** |

## Dependencies

- ✅ Prefect pipeline (Phase 1 complete)
- 🚧 LangChain integration (in progress)
- 📋 Hybrid storage (planned)

Can implement in **degraded mode** without hybrid storage (use current file cache), but full value requires semantic search.

## Success Criteria

- [ ] Command works in blind mode
- [ ] Command works in compare mode
- [ ] Confidence filtering works
- [ ] Results can be saved to file
- [ ] Output formats (JSON/YAML/text) work
- [ ] Uses Prefect caching (7-day TTL)
- [ ] Integrates with knowledge store
- [ ] All tests pass
- [ ] Documentation updated

## Future Enhancements

1. **Interactive mode**: Ask user to confirm/reject suggestions
2. **Batch mode**: Analyze multiple repos at once
3. **Learning**: Feed suggestions back to improve model
4. **GitHub integration**: Optionally create PR to add topics
5. **Topic templates**: Pre-defined topic sets for common domains
