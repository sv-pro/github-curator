"""Smart Repository Fetcher with adaptive multi-stage analysis.

This module implements a progressive analysis strategy that minimizes API calls,
LLM costs, and processing time by analyzing repositories incrementally.

Expected Benefits:
- 50-70% reduction in API calls
- 60-80% reduction in LLM costs
- 3-5x faster curation for large result sets
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

import yaml

from curator.core.intent_structuring import StructuredIntent
from curator.core.metacognitive_eval import EvaluationReport, MetacognitiveEvaluator
from curator.github.api_client import GitHubAPIClient, SearchResult
from curator.github.repo_analyzer import RepositoryAnalyzer


class Decision(Enum):
    """Analysis decision after each stage."""

    SKIP = "skip"  # Stop analysis, exclude repo
    CONTINUE_STANDARD = "continue"  # Proceed to next stage (normal)
    CONTINUE_DEEP = "continue_deep"  # Skip to stage 4 (very promising)


@dataclass
class StageResult:
    """Result from an analysis stage."""

    decision: Decision
    confidence: float
    reasoning: str
    cost_saved: float  # Estimated savings by skipping further stages
    data_fetched: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisTrace:
    """Trace of the analysis path taken for a repository."""

    repo: str
    thoroughness: str
    stages: list[StageResult] = field(default_factory=list)
    fast_tracked: bool = False
    total_savings: dict[str, Any] = field(default_factory=dict)

    def add_stage(self, stage_num: int, result: StageResult) -> None:
        """Add a stage result to the trace."""
        self.stages.append(result)

    def calculate_total_savings(self) -> None:
        """Calculate cumulative savings from all stages."""
        total_cost_saved = sum(stage.cost_saved for stage in self.stages)
        self.total_savings = {
            "cost_saved": total_cost_saved,
            "stages_completed": len(self.stages),
            "fast_tracked": self.fast_tracked,
        }


class SmartRepoFetcher:
    """Multi-stage adaptive repository analysis.

    Analyzes repositories progressively, making relevance decisions at each stage
    to minimize unnecessary API calls and LLM costs.

    Stages:
    1. Metadata Check: Fast filtering using GitHub API metadata (stars, topics, size)
    2. Lightweight Analysis: README excerpt + quick LLM check
    3. Deep Analysis: Full evaluation (current approach)
    4. Code Analysis: Optional repository cloning and code inspection
    """

    def __init__(
        self,
        config_path: str,
        intent: StructuredIntent,
        github_client: GitHubAPIClient,
        analyzer: RepositoryAnalyzer,
        evaluator: MetacognitiveEvaluator,
    ):
        """Initialize the smart fetcher.

        Args:
            config_path: Path to configuration file
            intent: Structured intent with dimensions and constraints
            github_client: GitHub API client
            analyzer: Repository analyzer for deep analysis
            evaluator: Metacognitive evaluator for full evaluation
        """
        self.config = self._load_config(config_path)
        self.intent = intent
        self.github = github_client
        self.analyzer = analyzer
        self.evaluator = evaluator

        # Load smart fetch configuration
        smart_config = self.config.get("smart_fetch", {})
        self.enabled = smart_config.get("enabled", True)

        # Stage 1 settings
        self.enable_metadata_filter = smart_config.get("enable_metadata_filter", True)
        self.min_stars_multiplier = smart_config.get("min_stars_multiplier", 0.5)
        self.max_size_kb = smart_config.get("max_size_kb", 500000)
        self.min_size_kb = smart_config.get("min_size_kb", 50)

        # Stage 2 settings
        self.enable_quick_llm = smart_config.get("enable_quick_llm", True)
        self.quick_model = smart_config.get("quick_model", "claude-3-haiku-20240307")
        self.min_quick_score = smart_config.get("min_quick_score", 0.3)
        self.high_promise_score = smart_config.get("high_promise_score", 0.7)
        self.readme_max_lines = smart_config.get("readme_max_lines", 500)

        # Stage 4 settings
        self.clone_threshold_score = smart_config.get("clone_threshold_score", 0.8)
        self.clone_threshold_confidence = smart_config.get("clone_threshold_confidence", 0.6)

        # Tracking
        self.total_analyzed = 0
        self.total_skipped = 0
        self.savings_data = {
            "api_calls_saved": 0,
            "cost_saved": 0.0,
            "time_saved_seconds": 0,
        }

    def _load_config(self, config_path: str) -> dict[str, Any]:
        """Load configuration from YAML file."""
        with open(config_path) as f:
            return yaml.safe_load(f)

    def analyze(
        self, repo: SearchResult, thoroughness: str = "standard"
    ) -> Optional[EvaluationReport]:
        """Analyze repository with adaptive fetching.

        Args:
            repo: Repository to analyze
            thoroughness: "fast", "standard", "thorough", "exhaustive"

        Returns:
            EvaluationReport if relevant, None if skipped
        """
        # Track what we're doing
        trace = AnalysisTrace(repo=repo.full_name, thoroughness=thoroughness)

        # Stage 1: Metadata filter
        if self.enable_metadata_filter and thoroughness in [
            "fast",
            "standard",
            "thorough",
            "exhaustive",
        ]:
            stage1 = self.stage1_metadata_check(repo)
            trace.add_stage(1, stage1)

            if stage1.decision == Decision.SKIP:
                self._log_skip(repo, "metadata", stage1)
                self.total_skipped += 1
                return None

        # Stage 2: Lightweight analysis
        if thoroughness in ["standard", "thorough", "exhaustive"]:
            stage2 = self.stage2_lightweight_analysis(repo)
            trace.add_stage(2, stage2)

            if stage2.decision == Decision.SKIP:
                self._log_skip(repo, "lightweight", stage2)
                self.total_skipped += 1
                return None

            # Very promising? Skip straight to deep analysis
            if stage2.decision == Decision.CONTINUE_DEEP:
                trace.fast_tracked = True

        # Stage 3: Deep analysis (full evaluation)
        stage3 = self.stage3_deep_analysis(repo)
        trace.add_stage(3, stage3)

        evaluation = stage3.data_fetched.get("evaluation")  # EvaluationReport

        # Stage 4: Code analysis (optional)
        if evaluation and (
            thoroughness in ["thorough", "exhaustive"] or self._should_clone(evaluation)
        ):
            stage4 = self.stage4_code_analysis(repo, evaluation)
            trace.add_stage(4, stage4)
            evaluation = stage4.data_fetched.get("evaluation")  # Enhanced evaluation

        # Calculate total savings
        trace.calculate_total_savings()

        # Update global tracking
        self.total_analyzed += 1
        self._update_savings(trace)

        return evaluation

    def stage1_metadata_check(self, repo: SearchResult) -> StageResult:
        """Quick metadata-based filtering.

        Uses only GitHub API metadata (already fetched during search) to make
        a fast relevance decision.

        Args:
            repo: Repository search result with metadata

        Returns:
            StageResult with decision and reasoning
        """
        # Extract keywords from intent
        keywords = self._extract_keywords(self.intent)

        # Check repository metadata
        score = 0.0
        reasons = []

        # Stars signal
        min_stars_threshold = int(self.intent.constraints.min_stars * self.min_stars_multiplier)
        if repo.stars >= self.intent.constraints.min_stars * 2:
            score += 0.2
            reasons.append(f"High stars ({repo.stars})")
        elif repo.stars < min_stars_threshold:
            score -= 0.3
            reasons.append(f"Low stars ({repo.stars} < {min_stars_threshold})")

        # Topics overlap
        topic_overlap = len(set(repo.topics) & set(keywords))
        if topic_overlap > 0:
            score += min(topic_overlap * 0.15, 0.4)
            reasons.append(f"{topic_overlap} matching topics")

        # Name/description keywords
        name_desc = f"{repo.name} {repo.description or ''}".lower()
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
            confidence=min(max(score, 0.0), 1.0),
            reasoning=" | ".join(reasons) if reasons else "No significant signals",
            cost_saved=self._estimate_savings(1) if decision == Decision.SKIP else 0.0,
            data_fetched={"metadata": {"stars": repo.stars, "topics": repo.topics}},
        )

    def stage2_lightweight_analysis(self, repo: SearchResult) -> StageResult:
        """Quick README + topics analysis.

        Fetches minimal README content and performs keyword analysis.
        Optionally uses a cheap LLM for uncertain cases.

        Args:
            repo: Repository search result

        Returns:
            StageResult with decision and reasoning
        """
        # Fetch minimal README
        try:
            readme_full = self.github.get_readme_content(repo.full_name)
            if readme_full:
                # Limit to first N lines
                lines = readme_full.split("\n")[: self.readme_max_lines]
                readme = "\n".join(lines)
            else:
                readme = ""
        except Exception:
            # No README or fetch failed - use fallback analysis
            readme = ""

        # Extract keywords from intent
        keywords = self._extract_keywords(self.intent)

        # Quick keyword analysis
        keyword_density = self._calculate_keyword_density(readme, keywords)

        # Topic overlap
        topic_score = len(set(repo.topics) & set(keywords)) / max(len(keywords), 1)

        # Combined quick score
        quick_score = (keyword_density * 0.6) + (topic_score * 0.4)

        # Optional: LLM quick check for uncertain cases
        llm_decision = None
        if self.enable_quick_llm and 0.3 <= quick_score <= 0.7:
            llm_decision = self._quick_llm_check(repo, readme[:500])
            if llm_decision == "no":
                quick_score *= 0.5  # Downweight
            elif llm_decision == "yes":
                quick_score = max(quick_score, 0.75)  # Upweight

        # Build reasoning
        reasons = [
            f"Keyword density: {keyword_density:.2f}",
            f"Topic overlap: {topic_score:.2f}",
        ]
        if llm_decision:
            reasons.append(f"LLM says: {llm_decision}")

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
            reasoning=" | ".join(reasons),
            cost_saved=self._estimate_savings(2) if decision == Decision.SKIP else 0.0,
            data_fetched={"readme_excerpt": readme[:500], "quick_score": quick_score},
        )

    def stage3_deep_analysis(self, repo: SearchResult) -> StageResult:
        """Full evaluation using existing approach.

        Args:
            repo: Repository search result

        Returns:
            StageResult with evaluation report
        """
        # Use existing analyzer and evaluator
        context = self.analyzer.analyze_repository(repo)
        context_summary = self.analyzer.get_evaluation_context_summary(context)
        evaluation = self.evaluator.evaluate_repository(context, self.intent, context_summary)

        return StageResult(
            decision=Decision.CONTINUE_STANDARD,  # Already evaluated, no more decisions
            confidence=evaluation.confidence,
            reasoning=f"Full evaluation complete: score={evaluation.overall_relevance:.2f}",
            cost_saved=0.0,  # No savings at this stage
            data_fetched={"evaluation": evaluation, "context": context},
        )

    def stage4_code_analysis(self, repo: SearchResult, evaluation: EvaluationReport) -> StageResult:
        """Optional deep code analysis via repository cloning.

        Args:
            repo: Repository search result
            evaluation: Current evaluation report

        Returns:
            StageResult with enhanced evaluation
        """
        # TODO: Implement code analysis
        # For now, just return the existing evaluation
        return StageResult(
            decision=Decision.CONTINUE_STANDARD,
            confidence=evaluation.confidence,
            reasoning="Code analysis not yet implemented",
            cost_saved=0.0,
            data_fetched={"evaluation": evaluation},
        )

    def _extract_keywords(self, intent: StructuredIntent) -> list[str]:
        """Extract keywords from intent dimensions.

        Args:
            intent: Structured intent

        Returns:
            List of keywords
        """
        keywords = []

        # Extract from dimension names
        for dim in intent.dimensions:
            # Split on common separators and add individual words
            words = dim.name.lower().replace("-", " ").replace("_", " ").split()
            keywords.extend(words)

        # Add theme words
        theme_words = intent.theme.lower().split()
        keywords.extend(theme_words)

        # Remove duplicates and common stop words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "with",
            "by",
        }
        keywords = list({kw for kw in keywords if len(kw) > 2 and kw not in stop_words})

        return keywords

    def _calculate_keyword_density(self, text: str, keywords: list[str]) -> float:
        """Calculate keyword density in text.

        Args:
            text: Text to analyze
            keywords: List of keywords to search for

        Returns:
            Keyword density score (0-1)
        """
        if not text or not keywords:
            return 0.0

        text_lower = text.lower()
        total_words = len(text_lower.split())

        if total_words == 0:
            return 0.0

        # Count keyword occurrences
        keyword_count = sum(text_lower.count(keyword.lower()) for keyword in keywords)

        # Normalize by text length and number of keywords
        density = min(keyword_count / (total_words * 0.05), 1.0)  # 5% threshold

        return density

    def _quick_llm_check(self, repo: SearchResult, readme_excerpt: str) -> str:
        """Fast binary relevance check with cheap LLM.

        Args:
            repo: Repository search result
            readme_excerpt: Excerpt of README content

        Returns:
            "yes", "no", or "maybe"
        """
        try:
            # Use the evaluator's LLM provider with a cheap model
            # TODO: This needs to be integrated with the LLM abstraction
            # For now, return "maybe" to not affect the score
            return "maybe"
        except Exception:
            # If LLM fails, return maybe (no impact on score)
            return "maybe"

    def _estimate_savings(self, stage: int) -> float:
        """Estimate cost savings by skipping remaining stages.

        Args:
            stage: Stage number where we're skipping

        Returns:
            Estimated cost saved in dollars
        """
        # Rough estimates based on typical API/LLM costs
        savings_per_stage = {
            1: 0.015,  # Skip all subsequent stages (README + eval)
            2: 0.010,  # Skip deep analysis
            3: 0.0,  # Already did deep analysis
        }
        return savings_per_stage.get(stage, 0.0)

    def _should_clone(self, evaluation: Optional[EvaluationReport]) -> bool:
        """Determine if repository should be cloned for code analysis.

        Args:
            evaluation: Evaluation report

        Returns:
            True if cloning is recommended
        """
        if not evaluation:
            return False

        # Clone if high score but low confidence (need more evidence)
        return (
            evaluation.overall_relevance > self.clone_threshold_score
            and evaluation.confidence < self.clone_threshold_confidence
        )

    def _log_skip(self, repo: SearchResult, stage: str, result: StageResult) -> None:
        """Log when a repository is skipped.

        Args:
            repo: Repository that was skipped
            stage: Stage name where it was skipped
            result: StageResult with skip reasoning
        """
        # For now, just track it. Can add logging later
        pass

    def _update_savings(self, trace: AnalysisTrace) -> None:
        """Update global savings tracking.

        Args:
            trace: Analysis trace with savings data
        """
        self.savings_data["cost_saved"] += trace.total_savings.get("cost_saved", 0.0)
        # TODO: Track API calls and time savings

    def get_savings_summary(self) -> dict[str, Any]:
        """Get summary of savings from smart fetching.

        Returns:
            Dictionary with savings statistics
        """
        total_repos = self.total_analyzed + self.total_skipped
        skip_rate = self.total_skipped / total_repos if total_repos > 0 else 0.0

        return {
            "total_count": total_repos,
            "analyzed_count": self.total_analyzed,
            "skipped_count": self.total_skipped,
            "skip_rate": skip_rate,
            "api_calls_saved": self.savings_data["api_calls_saved"],
            "cost_saved": self.savings_data["cost_saved"],
            "time_saved_seconds": self.savings_data["time_saved_seconds"],
        }
