# Feature: Smart Repository Fetcher

## Overview

The Smart Repository Fetcher is an adaptive, multi-stage analysis strategy that avoids brute-force repository evaluation by making progressive relevance decisions. It minimizes API calls, LLM costs, and processing time by analyzing repositories incrementally—fetching only as much data as needed to make confident relevance decisions.

## Status

**Currently**: Not implemented
**Priority**: P2 (Medium - optimization feature)
**Dependencies**: None (can be implemented independently)
**Estimated Effort**: 2-3 days

## Problem Statement

### Current Approach (Brute Force)

The current curation pipeline evaluates every repository with the same depth:

1. Fetch full README
2. Fetch file structure
3. Fetch additional documentation files
4. Clone repository (if --use-git-clone)
5. Perform full LLM evaluation

**Problems**:
- Wastes API calls on clearly irrelevant repositories
- Expensive LLM calls for repos that could be filtered early
- Slow for large result sets (100+ repos)
- Same processing cost regardless of relevance

**Example**: When curating "AI agents with tool use", we spend full evaluation costs on repositories like:
- "my-first-chatbot" (toy project, 10 stars)
- "awesome-python" (list, not implementation)
- "web-scraper" (unrelated topic)

### Desired Approach (Smart Fetching)

**Progressive disclosure**: Start lightweight, dig deeper only when promising.

```
Candidate repo
    ↓
[Stage 1: Metadata Check] (GitHub API only, free)
    ↓ relevant?
    ├─ No → SKIP (saved 90% of work)
    └─ Yes/Maybe → Continue
         ↓
[Stage 2: Lightweight Analysis] (README + topics, cheap)
    ↓ promising?
    ├─ No → SKIP (saved 70% of work)
    └─ Yes → Continue
         ↓
[Stage 3: Deep Analysis] (full evaluation, expensive)
    ↓
[Stage 4: Code Analysis] (clone + analyze, very expensive)
```

**Benefits**:
- 50-70% reduction in API calls
- 60-80% reduction in LLM costs
- 3-5x faster curation for large result sets
- Same or better accuracy (early filtering prevents noise)

---

## Design

### Stage 1: Metadata Check (Fast Filter)

**Data Sources**: GitHub API metadata only (already fetched during search)

**What to check**:
- Stars count vs. minimum threshold
- Last update date vs. max age
- Language match (if specified)
- Has license (if required)
- Repository size (skip very small or very large)
- Topics list (quick keyword match)

**Decision**:
- **SKIP** if: clearly fails basic criteria
- **CONTINUE** otherwise

**Cost**: Essentially free (data already available)

**Example filters**:
```python
# Skip if obviously irrelevant
if repo.stars < min_stars / 2:  # Way below threshold
    return Decision.SKIP

if "tutorial" in repo.name.lower() and repo.stars < 100:
    return Decision.SKIP

if repo.size_kb < 50:  # Too small to be substantial
    return Decision.SKIP
```

### Stage 2: Lightweight Analysis (Quick Relevance Check)

**Data Sources**:
- README.md (first 500 lines or 50KB)
- Repository topics (GitHub API)
- Root-level documentation files (list only, not content)

**What to check**:
- README keyword matching (intent dimensions → keywords)
- Topics overlap with intent
- Presence of documentation structure
- Quick LLM query: "Does this repo relate to [theme]? (yes/no/maybe)"

**Decision**:
- **SKIP** if: clearly irrelevant (high confidence)
- **CONTINUE** if: relevant or uncertain

**Cost**: 1 GitHub API call + 1 cheap LLM call (~100 tokens)

**Example analysis**:
```python
# Extract keywords from intent dimensions
keywords = extract_keywords(intent.dimensions)

# Check README for keyword density
readme_excerpt = fetch_readme(repo, max_lines=500)
keyword_matches = count_keyword_matches(readme_excerpt, keywords)

# Check topics overlap
topic_overlap = len(set(repo.topics) & set(intent.related_topics))

# Quick relevance score
quick_score = (keyword_matches * 0.6) + (topic_overlap * 0.4)

if quick_score < 0.3:
    return Decision.SKIP
elif quick_score > 0.7:
    return Decision.CONTINUE_DEEP
else:
    return Decision.CONTINUE_STANDARD
```

**LLM Quick Check** (optional, for uncertain cases):
```python
# Use fast, cheap model for binary decision
response = llm.invoke(
    model="claude-3-haiku-20240307",  # Cheapest model
    messages=[{
        "role": "user",
        "content": f"""
        Theme: {intent.theme}
        Repository: {repo.name}
        Topics: {repo.topics}
        README excerpt: {readme_excerpt[:500]}

        Question: Is this repository relevant to the theme?
        Answer with ONLY: yes, no, or maybe
        """
    }],
    max_tokens=10
)

if response.lower() == "no":
    return Decision.SKIP
```

### Stage 3: Deep Analysis (Full Evaluation - Current Approach)

**Data Sources**:
- Full README
- File structure analysis
- Key documentation files (ARCHITECTURE.md, docs/, examples/)
- Comprehensive LLM evaluation

**What to check**:
- Full metacognitive evaluation (current approach)
- All dimensions scored with evidence
- Confidence tracking

**Decision**:
- **INCLUDE** with score and confidence
- **OPTIONAL**: Proceed to Stage 4 for code analysis if:
  - Score > 0.8 AND confidence < 0.6 (high potential, need more data)
  - User specified --thorough or --use-git-clone

**Cost**: 2-3 GitHub API calls + 1 expensive LLM call (~2000-5000 tokens)

### Stage 4: Code Analysis (Very Deep - Optional)

**Data Sources**:
- Full repository clone
- Code structure analysis
- Test coverage, CI configuration
- Actual implementation patterns

**What to check**:
- Architectural patterns (from code, not just docs)
- Test quality and coverage
- Dependency analysis
- Code quality metrics

**Decision**:
- **ENHANCE** evaluation with code-derived evidence
- Update confidence scores

**Cost**: Git clone + local analysis + potential LLM calls

**When to use**:
- User explicitly requested (--use-git-clone)
- OR high-value repos with incomplete documentation
- OR --thorough mode enabled

---

## Implementation

### Core Classes

```python
# curator/github/smart_fetcher.py

from dataclasses import dataclass
from enum import Enum
from typing import Optional

class Decision(Enum):
    """Analysis decision after each stage."""
    SKIP = "skip"                    # Stop analysis, exclude repo
    CONTINUE_STANDARD = "continue"   # Proceed to next stage (normal)
    CONTINUE_DEEP = "continue_deep"  # Skip to stage 4 (very promising)

@dataclass
class StageResult:
    """Result from an analysis stage."""
    decision: Decision
    confidence: float
    reasoning: str
    cost_saved: float  # Estimated savings by skipping further stages
    data_fetched: dict  # What data was actually fetched

class SmartRepoFetcher:
    """Multi-stage adaptive repository analysis."""

    def __init__(self, config, intent, github_client, llm_provider):
        self.config = config
        self.intent = intent
        self.github = github_client
        self.llm = llm_provider

        # Stage settings from config
        self.enable_metadata_filter = config.get("smart_fetch", {}).get("enable_metadata_filter", True)
        self.enable_quick_llm = config.get("smart_fetch", {}).get("enable_quick_llm", True)
        self.quick_llm_model = config.get("smart_fetch", {}).get("quick_model", "claude-3-haiku-20240307")

        # Thresholds
        self.min_quick_score = config.get("smart_fetch", {}).get("min_quick_score", 0.3)
        self.high_promise_score = config.get("smart_fetch", {}).get("high_promise_score", 0.7)

    def analyze(self, repo: SearchResult, thoroughness: str = "standard") -> Optional[EvaluationReport]:
        """
        Analyze repository with adaptive fetching.

        Args:
            repo: Repository to analyze
            thoroughness: "fast", "standard", "thorough", "exhaustive"

        Returns:
            EvaluationReport if relevant, None if skipped
        """
        # Track what we're doing
        trace = AnalysisTrace(repo=repo.full_name, thoroughness=thoroughness)

        # Stage 1: Metadata filter
        if self.enable_metadata_filter:
            stage1 = self.stage1_metadata_check(repo)
            trace.add_stage(1, stage1)

            if stage1.decision == Decision.SKIP:
                self.log_skip(repo, "metadata", stage1)
                return None

        # Stage 2: Lightweight analysis
        if thoroughness in ["standard", "thorough", "exhaustive"]:
            stage2 = self.stage2_lightweight_analysis(repo)
            trace.add_stage(2, stage2)

            if stage2.decision == Decision.SKIP:
                self.log_skip(repo, "lightweight", stage2)
                return None

            # Very promising? Skip straight to deep analysis
            if stage2.decision == Decision.CONTINUE_DEEP:
                trace.fast_tracked = True

        # Stage 3: Deep analysis (full evaluation)
        stage3 = self.stage3_deep_analysis(repo)
        trace.add_stage(3, stage3)

        evaluation = stage3.evaluation  # EvaluationReport

        # Stage 4: Code analysis (optional)
        if thoroughness in ["thorough", "exhaustive"] or self._should_clone(evaluation):
            stage4 = self.stage4_code_analysis(repo, evaluation)
            trace.add_stage(4, stage4)
            evaluation = stage4.evaluation  # Enhanced evaluation

        # Save trace for analysis
        trace.save()

        return evaluation

    def stage1_metadata_check(self, repo: SearchResult) -> StageResult:
        """Quick metadata-based filtering."""
        # Extract keywords from intent
        keywords = self._extract_keywords(self.intent)

        # Check repository metadata
        score = 0.0
        reasons = []

        # Stars signal
        if repo.stars >= self.intent.constraints.min_stars * 2:
            score += 0.2
            reasons.append(f"High stars ({repo.stars})")

        # Topics overlap
        topic_overlap = len(set(repo.topics) & set(keywords))
        if topic_overlap > 0:
            score += min(topic_overlap * 0.15, 0.4)
            reasons.append(f"{topic_overlap} matching topics")

        # Size check (too small = toy project)
        if repo.size_kb < 50:
            score -= 0.3
            reasons.append("Very small repo")

        # Name/description keywords
        name_desc = f"{repo.name} {repo.description}".lower()
        keyword_hits = sum(1 for kw in keywords if kw.lower() in name_desc)
        if keyword_hits > 0:
            score += min(keyword_hits * 0.1, 0.3)
            reasons.append(f"{keyword_hits} keywords in name/desc")

        # Decision
        if score < 0.2:
            decision = Decision.SKIP
        else:
            decision = Decision.CONTINUE_STANDARD

        return StageResult(
            decision=decision,
            confidence=min(score, 1.0),
            reasoning=" | ".join(reasons),
            cost_saved=self._estimate_savings(1) if decision == Decision.SKIP else 0,
            data_fetched={"metadata": repo.__dict__}
        )

    def stage2_lightweight_analysis(self, repo: SearchResult) -> StageResult:
        """Quick README + topics analysis."""
        # Fetch minimal README
        readme = self.github.get_readme(repo.full_name, max_lines=500)

        # Quick keyword analysis
        keywords = self._extract_keywords(self.intent)
        keyword_density = self._calculate_keyword_density(readme, keywords)

        # Topic overlap
        topic_score = len(set(repo.topics) & set(keywords)) / max(len(keywords), 1)

        # Combined quick score
        quick_score = (keyword_density * 0.6) + (topic_score * 0.4)

        # Optional: LLM quick check for uncertain cases
        if self.enable_quick_llm and 0.3 <= quick_score <= 0.7:
            llm_decision = self._quick_llm_check(repo, readme)
            if llm_decision == "no":
                quick_score *= 0.5  # Downweight
            elif llm_decision == "yes":
                quick_score = max(quick_score, 0.75)  # Upweight

        # Decision
        if quick_score < self.min_quick_score:
            decision = Decision.SKIP
        elif quick_score > self.high_promise_score:
            decision = Decision.CONTINUE_DEEP
        else:
            decision = Decision.CONTINUE_STANDARD

        return StageResult(
            decision=decision,
            confidence=quick_score,
            reasoning=f"Keyword density: {keyword_density:.2f}, Topic overlap: {topic_score:.2f}",
            cost_saved=self._estimate_savings(2) if decision == Decision.SKIP else 0,
            data_fetched={"readme_excerpt": readme[:500]}
        )

    def _quick_llm_check(self, repo: SearchResult, readme: str) -> str:
        """Fast binary relevance check with cheap LLM."""
        response = self.llm.invoke(
            model=self.quick_llm_model,
            messages=[{
                "role": "user",
                "content": f"""
                Theme: {self.intent.theme}
                Repository: {repo.name}
                Topics: {', '.join(repo.topics)}
                README excerpt: {readme[:500]}

                Is this repository relevant to the theme?
                Answer ONLY: yes, no, or maybe
                """
            }],
            max_tokens=10
        )
        return response.strip().lower()

    # ... additional methods ...
```

### Configuration

```yaml
# config/curator.yaml

smart_fetch:
  # Enable smart fetching (vs. brute force)
  enabled: true

  # Stage 1: Metadata filtering
  enable_metadata_filter: true
  min_stars_multiplier: 0.5  # Skip if < 50% of min_stars
  max_size_kb: 500000        # Skip huge repos (500MB+)
  min_size_kb: 50            # Skip tiny repos

  # Stage 2: Lightweight analysis
  enable_quick_llm: true
  quick_model: "claude-3-haiku-20240307"  # Cheapest model
  min_quick_score: 0.3       # Skip if relevance < 30%
  high_promise_score: 0.7    # Fast-track if > 70%
  readme_max_lines: 500      # Read only first N lines

  # Stage 3: Deep analysis
  # (use existing evaluation settings)

  # Stage 4: Code analysis
  clone_threshold_score: 0.8      # Clone if score > 0.8
  clone_threshold_confidence: 0.6 # AND confidence < 0.6

  # Thoroughness presets
  thoroughness:
    fast:
      - metadata_filter
      - lightweight_analysis
      - deep_analysis  # limited

    standard:  # Default
      - metadata_filter
      - lightweight_analysis
      - deep_analysis  # full

    thorough:
      - metadata_filter
      - lightweight_analysis
      - deep_analysis
      - code_analysis  # selective

    exhaustive:
      - metadata_filter
      - lightweight_analysis
      - deep_analysis
      - code_analysis  # all repos
```

### CLI Integration

```python
# curator/__main__.py

@cli.command()
@click.argument("theme")
# ... existing options ...
@click.option(
    "--fetch-mode",
    type=click.Choice(["fast", "standard", "thorough", "exhaustive"]),
    default="standard",
    help="Analysis depth: fast (quick filter) | standard (balanced) | thorough (deep) | exhaustive (all)"
)
@click.option(
    "--disable-smart-fetch",
    is_flag=True,
    help="Disable smart fetching, analyze all repos fully (brute force)"
)
def curate(theme, fetch_mode, disable_smart_fetch, ...):
    """Curate GitHub repositories based on a theme."""

    # Initialize smart fetcher
    if disable_smart_fetch:
        fetcher = BruteForceFetcher(...)  # Old behavior
    else:
        fetcher = SmartRepoFetcher(config, intent, github_client, llm_provider)

    # Analyze repos
    for repo in candidate_repos:
        evaluation = fetcher.analyze(repo, thoroughness=fetch_mode)

        if evaluation:  # Not skipped
            evaluations.append(evaluation)
        else:
            skipped_count += 1

    # Show savings
    if not disable_smart_fetch:
        savings = fetcher.get_savings_summary()
        click.echo(f"\n💰 Smart Fetch Savings:")
        click.echo(f"   Repos skipped: {savings.skipped_count} / {savings.total_count} ({savings.skip_rate:.0%})")
        click.echo(f"   API calls saved: {savings.api_calls_saved}")
        click.echo(f"   Cost saved: ${savings.cost_saved:.2f}")
        click.echo(f"   Time saved: {savings.time_saved_seconds:.0f}s")
```

---

## Metrics & Evaluation

### Success Metrics

After implementation, track:

1. **Efficiency Gains**:
   - API calls saved (target: 50-70%)
   - LLM costs saved (target: 60-80%)
   - Time saved (target: 3-5x speedup)

2. **Accuracy**:
   - False negatives: relevant repos incorrectly skipped (target: <5%)
   - False positives: irrelevant repos not skipped (acceptable)
   - Precision: % of included repos that are relevant (target: maintain current)

3. **User Experience**:
   - Faster results (measure total curation time)
   - Clear feedback on what was skipped and why
   - Ability to override (--disable-smart-fetch, --thorough)

### Testing Strategy

1. **Baseline Comparison**:
   - Run same theme with brute force vs. smart fetch
   - Compare results, costs, and timing

2. **False Negative Detection**:
   - Sample skipped repos manually
   - Verify they were correctly skipped
   - Adjust thresholds if needed

3. **Threshold Tuning**:
   - Experiment with different score thresholds
   - Find sweet spot: max savings, min false negatives

---

## Migration Path

### Phase 1: Foundation (3 days)
- [ ] Implement `SmartRepoFetcher` class
- [ ] Add Stage 1 (metadata) and Stage 2 (lightweight)
- [ ] Basic testing and threshold tuning

### Phase 2: Integration (1 day)
- [ ] Integrate into CLI
- [ ] Add configuration options
- [ ] Update documentation

### Phase 3: Optimization (1 day)
- [ ] Add metrics tracking
- [ ] Tune thresholds based on real data
- [ ] Add detailed logging and trace output

### Phase 4: Advanced Features (optional, 2 days)
- [ ] Stage 4 code analysis
- [ ] Machine learning for threshold optimization
- [ ] Adaptive thresholds based on intent complexity

---

## Future Enhancements

1. **Learning from History**:
   - Track which repos were skipped vs. included
   - Learn patterns: "repos with X metadata pattern are usually Y relevant"
   - Auto-tune thresholds

2. **Intent-Specific Strategies**:
   - Different fetching strategies for different intent types
   - "AI agents" → focus on architecture docs
   - "Web frameworks" → focus on README + examples

3. **Cost-Aware Fetching**:
   - Dynamic thresholds based on remaining budget
   - More aggressive filtering when budget is low
   - Thorough analysis when budget is high

4. **Parallel Stage Execution**:
   - Fetch README while analyzing metadata
   - Pipeline stages for better throughput

---

## Open Questions

1. **Default behavior**: Should smart fetch be enabled by default or opt-in?
   - **Recommendation**: Default enabled, allow --disable-smart-fetch to opt out

2. **LLM quick check**: Always use or only for uncertain cases?
   - **Recommendation**: Only for 0.3-0.7 score range (uncertain)

3. **Threshold tuning**: Manual or automatic?
   - **Recommendation**: Start manual, add auto-tuning in Phase 4

4. **Stage 4 triggers**: When to clone repositories?
   - **Recommendation**: Only in "thorough" mode or user-requested

---

## References

- Original task: `github-curator.todo` item #3
- Related: `docs/features/declarative-pipeline.md` (caching strategy)
- Related: `docs/features/cost-tracking.md` (cost optimization)
- TODO item: Listed in `TODO.md` under "New Features"
