"""Reflection module - analyzes patterns and suggests improvements."""

import statistics
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import yaml

from curator.core.intent_structuring import StructuredIntent
from curator.core.metacognitive_eval import EvaluationReport


@dataclass
class Pattern:
    """A detected pattern in evaluations."""

    pattern_type: str
    description: str
    frequency: float
    reason: str
    recommendation: str
    affected_items: list[str] = field(default_factory=list)


@dataclass
class IntentImprovement:
    """Suggested improvement to intent structure."""

    improvement_type: str
    dimension: str
    details: dict[str, Any]
    reason: str


@dataclass
class ProcessImprovement:
    """Suggested improvement to evaluation process."""

    recommendation: str
    expected_impact: str
    implementation: str


@dataclass
class ReflectionReport:
    """Complete reflection report on evaluations."""

    reflection_id: str
    based_on_evaluations: int
    timestamp: str
    insights: list[Pattern]
    suggested_intent_improvements: list[IntentImprovement]
    process_improvements: list[ProcessImprovement]
    correlations: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "reflection_id": self.reflection_id,
            "based_on_evaluations": self.based_on_evaluations,
            "timestamp": self.timestamp,
            "insights": [
                {
                    "pattern": p.pattern_type,
                    "description": p.description,
                    "frequency": p.frequency,
                    "reason": p.reason,
                    "recommendation": p.recommendation,
                    "affected_items": p.affected_items,
                }
                for p in self.insights
            ],
            "suggested_intent_improvements": [
                {
                    "type": imp.improvement_type,
                    "dimension": imp.dimension,
                    "details": imp.details,
                    "reason": imp.reason,
                }
                for imp in self.suggested_intent_improvements
            ],
            "process_improvements": [
                {
                    "recommendation": pi.recommendation,
                    "expected_impact": pi.expected_impact,
                    "implementation": pi.implementation,
                }
                for pi in self.process_improvements
            ],
            "correlations": self.correlations,
        }


class Reflector:
    """Analyzes evaluation patterns and suggests improvements."""

    def __init__(self, config_path: str = "config/curator.yaml"):
        """Initialize reflector."""
        self.config = self._load_config(config_path)
        self.min_evaluations = self.config["reflection"]["min_evaluations_for_patterns"]
        self.correlation_threshold = self.config["reflection"]["correlation_threshold"]

    def _load_config(self, config_path: str) -> dict[str, Any]:
        """Load configuration from YAML file."""
        with open(config_path) as f:
            return yaml.safe_load(f)

    def reflect(
        self, evaluations: list[EvaluationReport], intent: StructuredIntent
    ) -> ReflectionReport:
        """Analyze evaluations and generate insights.

        Args:
            evaluations: List of evaluation reports
            intent: Original structured intent

        Returns:
            ReflectionReport with patterns and suggestions
        """
        if len(evaluations) < self.min_evaluations:
            return ReflectionReport(
                reflection_id=str(uuid.uuid4()),
                based_on_evaluations=len(evaluations),
                timestamp=datetime.utcnow().isoformat(),
                insights=[],
                suggested_intent_improvements=[],
                process_improvements=[],
                correlations={},
            )

        # Detect patterns
        insights = self._detect_patterns(evaluations, intent)

        # Suggest intent improvements
        intent_improvements = self._suggest_intent_improvements(evaluations, intent, insights)

        # Suggest process improvements
        process_improvements = self._suggest_process_improvements(evaluations, intent)

        # Calculate correlations
        correlations = self._calculate_correlations(evaluations)

        return ReflectionReport(
            reflection_id=str(uuid.uuid4()),
            based_on_evaluations=len(evaluations),
            timestamp=datetime.utcnow().isoformat(),
            insights=insights,
            suggested_intent_improvements=intent_improvements,
            process_improvements=process_improvements,
            correlations=correlations,
        )

    def _detect_patterns(
        self, evaluations: list[EvaluationReport], intent: StructuredIntent
    ) -> list[Pattern]:
        """Detect patterns in evaluations."""
        patterns = []

        # Pattern 1: Low confidence dimensions
        dimension_confidences = defaultdict(list)
        for eval in evaluations:
            for ds in eval.dimension_scores:
                dimension_confidences[ds.dimension].append(ds.confidence)

        for dim_name, confidences in dimension_confidences.items():
            avg_conf = statistics.mean(confidences)
            low_conf_count = sum(1 for c in confidences if c < 0.5)
            low_conf_freq = low_conf_count / len(confidences)

            if low_conf_freq > 0.5:
                patterns.append(
                    Pattern(
                        pattern_type="low_confidence_dimension",
                        description=f"Dimension '{dim_name}' frequently has low confidence",
                        frequency=low_conf_freq,
                        reason=f"Average confidence: {avg_conf:.2f}, {low_conf_freq*100:.0f}% below 0.5",
                        recommendation=f"Review indicators for '{dim_name}' - may need more detectable criteria",
                        affected_items=[dim_name],
                    )
                )

        # Pattern 2: Unused indicators
        indicator_usage: dict[str, int] = defaultdict(int)
        total_evals = len(evaluations)

        for eval in evaluations:
            for ds in eval.dimension_scores:
                for ind in ds.found_indicators:
                    indicator_usage[f"{ds.dimension}::{ind.indicator}"] += 1

        for dim in intent.dimensions:
            for indicator in dim.indicators:
                key = f"{dim.name}::{indicator.name}"
                usage_freq = indicator_usage.get(key, 0) / total_evals

                if usage_freq < 0.2:
                    patterns.append(
                        Pattern(
                            pattern_type="unused_indicator",
                            description=f"Indicator '{indicator.name}' rarely found",
                            frequency=usage_freq,
                            reason=f"Found in only {usage_freq*100:.0f}% of evaluations",
                            recommendation=f"Consider replacing '{indicator.name}' with more detectable indicator",
                            affected_items=[dim.name, indicator.name],
                        )
                    )

        # Pattern 3: Consistently high/low scoring dimensions
        dimension_scores = defaultdict(list)
        for eval in evaluations:
            for ds in eval.dimension_scores:
                dimension_scores[ds.dimension].append(ds.score)

        for dim_name, scores in dimension_scores.items():
            avg_score = statistics.mean(scores)
            std_dev = statistics.stdev(scores) if len(scores) > 1 else 0

            if avg_score > 0.8 and std_dev < 0.1:
                patterns.append(
                    Pattern(
                        pattern_type="non_discriminating_dimension",
                        description=f"Dimension '{dim_name}' consistently scores high",
                        frequency=1.0,
                        reason=f"Average score: {avg_score:.2f}, low variance (σ={std_dev:.2f})",
                        recommendation=f"'{dim_name}' may not be discriminating - consider adjusting criteria",
                        affected_items=[dim_name],
                    )
                )

        return patterns

    def _suggest_intent_improvements(
        self, evaluations: list[EvaluationReport], intent: StructuredIntent, insights: list[Pattern]
    ) -> list[IntentImprovement]:
        """Suggest improvements to intent structure."""
        improvements = []

        # Improvement 1: Remove unused indicators
        for pattern in insights:
            if pattern.pattern_type == "unused_indicator":
                dim_name, ind_name = pattern.affected_items
                improvements.append(
                    IntentImprovement(
                        improvement_type="remove_indicator",
                        dimension=dim_name,
                        details={"indicator": ind_name},
                        reason=f"Indicator '{ind_name}' found in only {pattern.frequency*100:.0f}% of evaluations",
                    )
                )

        # Improvement 2: Adjust weights for non-discriminating dimensions
        for pattern in insights:
            if pattern.pattern_type == "non_discriminating_dimension":
                dim_name = pattern.affected_items[0]
                current_weight = next(d.weight for d in intent.dimensions if d.name == dim_name)
                suggested_weight = max(0.1, current_weight * 0.7)  # Reduce by 30%

                improvements.append(
                    IntentImprovement(
                        improvement_type="adjust_weight",
                        dimension=dim_name,
                        details={"from": current_weight, "to": suggested_weight},
                        reason="Dimension not discriminating - scores consistently high",
                    )
                )

        # Improvement 3: Add indicators for low confidence dimensions
        for pattern in insights:
            if pattern.pattern_type == "low_confidence_dimension":
                dim_name = pattern.affected_items[0]
                improvements.append(
                    IntentImprovement(
                        improvement_type="add_indicators",
                        dimension=dim_name,
                        details={"suggestion": "Add more concrete, detectable indicators"},
                        reason=f"Low confidence ({pattern.frequency*100:.0f}% of evals) suggests indicators are hard to detect",
                    )
                )

        return improvements

    def _suggest_process_improvements(
        self, evaluations: list[EvaluationReport], intent: StructuredIntent
    ) -> list[ProcessImprovement]:
        """Suggest improvements to evaluation process."""
        improvements = []

        # Check context completeness
        low_context_count = sum(
            1 for e in evaluations if e.metacognitive_notes.context_completeness < 0.5
        )

        if low_context_count / len(evaluations) > 0.3:
            improvements.append(
                ProcessImprovement(
                    recommendation="Expand context gathering to include more files",
                    expected_impact=f"Improve context completeness for ~{low_context_count} repos",
                    implementation="Add more files to context_files config (e.g., tests/, docs/architecture/)",
                )
            )

        # Check for common limitations
        limitation_counts: dict[str, int] = defaultdict(int)
        for eval in evaluations:
            for limitation in eval.metacognitive_notes.limitations:
                limitation_counts[limitation] += 1

        for limitation, count in limitation_counts.items():
            if count / len(evaluations) > 0.4:
                improvements.append(
                    ProcessImprovement(
                        recommendation=f"Address common limitation: {limitation}",
                        expected_impact=f"Affects {count}/{len(evaluations)} evaluations",
                        implementation="Adjust context gathering or fallback analysis methods",
                    )
                )

        return improvements

    def _calculate_correlations(self, evaluations: list[EvaluationReport]) -> dict[str, Any]:
        """Calculate correlations between metrics."""
        correlations = {}

        # Extract data
        stars = []
        overall_scores = []
        dimension_scores = defaultdict(list)

        for eval in evaluations:
            stars.append(eval.metadata.stars if hasattr(eval, "metadata") else 0)
            overall_scores.append(eval.overall_relevance)

            for ds in eval.dimension_scores:
                dimension_scores[ds.dimension].append(ds.score)

        # Calculate star correlation with overall score
        if len(stars) > 2 and len(set(stars)) > 1:
            star_score_corr = self._pearson_correlation(stars, overall_scores)
            if abs(star_score_corr) > self.correlation_threshold:
                correlations["stars_vs_score"] = {
                    "correlation": round(star_score_corr, 2),
                    "interpretation": "strong" if abs(star_score_corr) > 0.7 else "moderate",
                }

        # Calculate dimension correlations
        dim_correlations = {}
        dim_names = list(dimension_scores.keys())
        for i, dim1 in enumerate(dim_names):
            for dim2 in dim_names[i + 1 :]:
                if len(dimension_scores[dim1]) > 2:
                    corr = self._pearson_correlation(dimension_scores[dim1], dimension_scores[dim2])
                    if abs(corr) > self.correlation_threshold:
                        dim_correlations[f"{dim1}_vs_{dim2}"] = round(corr, 2)

        if dim_correlations:
            correlations["dimension_correlations"] = dim_correlations  # type: ignore[assignment]

        return correlations

    def _pearson_correlation(self, x: list[float], y: list[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        if len(x) != len(y) or len(x) < 2:
            return 0.0

        n = len(x)
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(y)

        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        denominator_x = sum((x[i] - mean_x) ** 2 for i in range(n))
        denominator_y = sum((y[i] - mean_y) ** 2 for i in range(n))

        if denominator_x == 0 or denominator_y == 0:
            return 0.0

        return numerator / ((denominator_x * denominator_y) ** 0.5)
