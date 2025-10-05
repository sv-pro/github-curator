"""Metacognitive evaluation module - evaluates repositories with explicit confidence tracking."""

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import anthropic
import yaml

from curator.core.intent_structuring import Dimension, StructuredIntent
from curator.github.repo_analyzer import RepositoryContext


@dataclass
class IndicatorEvidence:
    """Evidence for a specific indicator."""

    indicator: str
    evidence: str
    location: str
    confidence: float


@dataclass
class DimensionScore:
    """Score for a single evaluation dimension."""

    dimension: str
    score: float
    confidence: float
    found_indicators: list[IndicatorEvidence]
    missing_indicators: list[str]
    reasoning: str


@dataclass
class MetacognitiveNotes:
    """Metacognitive reflection on the evaluation."""

    context_completeness: float
    limitations: list[str]
    confidence_factors: dict[str, list[str]]


@dataclass
class EvaluationReport:
    """Complete evaluation report for a repository."""

    repo: str
    intent_id: str
    evaluated_at: str
    overall_relevance: float
    confidence: float
    dimension_scores: list[DimensionScore]
    metacognitive_notes: MetacognitiveNotes
    recommendation: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "repo": self.repo,
            "intent_id": self.intent_id,
            "evaluated_at": self.evaluated_at,
            "overall_relevance": self.overall_relevance,
            "confidence": self.confidence,
            "dimension_scores": [
                {
                    "dimension": ds.dimension,
                    "score": ds.score,
                    "confidence": ds.confidence,
                    "found_indicators": [
                        {
                            "indicator": ie.indicator,
                            "evidence": ie.evidence,
                            "location": ie.location,
                            "confidence": ie.confidence,
                        }
                        for ie in ds.found_indicators
                    ],
                    "missing_indicators": ds.missing_indicators,
                    "reasoning": ds.reasoning,
                }
                for ds in self.dimension_scores
            ],
            "metacognitive_notes": {
                "context_completeness": self.metacognitive_notes.context_completeness,
                "limitations": self.metacognitive_notes.limitations,
                "confidence_factors": self.metacognitive_notes.confidence_factors,
            },
            "recommendation": self.recommendation,
            "notes": self.notes,
        }


class MetacognitiveEvaluator:
    """Evaluates repositories with explicit confidence and metacognitive tracking."""

    def __init__(self, config_path: str = "config/curator.yaml"):
        """Initialize evaluator."""
        self.config = self._load_config(config_path)
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def _load_config(self, config_path: str) -> dict[str, Any]:
        """Load configuration from YAML file."""
        with open(config_path) as f:
            return yaml.safe_load(f)

    def evaluate_repository(
        self, context: RepositoryContext, intent: StructuredIntent, context_summary: str
    ) -> EvaluationReport:
        """Evaluate a repository against structured intent.

        Args:
            context: Repository context
            intent: Structured intent with dimensions
            context_summary: Text summary of repository for LLM

        Returns:
            EvaluationReport with scores, evidence, and metacognitive notes
        """
        # Evaluate each dimension
        dimension_scores = []
        for dimension in intent.dimensions:
            score = self._evaluate_dimension(dimension, context_summary, intent.theme)
            dimension_scores.append(score)

        # Calculate overall relevance (weighted average)
        overall_relevance = sum(
            ds.score * next(d.weight for d in intent.dimensions if d.name == ds.dimension)
            for ds in dimension_scores
        )

        # Calculate overall confidence (weighted average)
        overall_confidence = sum(
            ds.confidence * next(d.weight for d in intent.dimensions if d.name == ds.dimension)
            for ds in dimension_scores
        )

        # Generate metacognitive notes
        metacognitive_notes = self._generate_metacognitive_notes(
            dimension_scores, context, overall_confidence
        )

        # Determine recommendation
        recommendation = self._determine_recommendation(
            overall_relevance, overall_confidence, dimension_scores
        )

        # Generate summary notes
        notes = self._generate_notes(dimension_scores, overall_relevance, overall_confidence)

        return EvaluationReport(
            repo=context.full_name,
            intent_id=intent.intent_id,
            evaluated_at=datetime.utcnow().isoformat(),
            overall_relevance=round(overall_relevance, 2),
            confidence=round(overall_confidence, 2),
            dimension_scores=dimension_scores,
            metacognitive_notes=metacognitive_notes,
            recommendation=recommendation,
            notes=notes,
        )

    def _evaluate_dimension(
        self, dimension: Dimension, context_summary: str, theme: str
    ) -> DimensionScore:
        """Evaluate a single dimension using Claude.

        Args:
            dimension: Dimension to evaluate
            context_summary: Repository context summary
            theme: Original curation theme

        Returns:
            DimensionScore with evidence and confidence
        """
        indicators_text = "\n".join(
            [f"- {ind.name}: {ind.description}" for ind in dimension.indicators]
        )

        prompt = f"""You are evaluating a GitHub repository for the dimension "{dimension.name}" as part of curating repositories for: "{theme}"

Repository Context:
{context_summary}

Dimension: {dimension.name}
Indicators to look for:
{indicators_text}

For each indicator, determine:
1. Is there evidence of this indicator in the repository?
2. What specific evidence supports it?
3. Where was the evidence found?
4. How confident are you in this finding? (0.0-1.0)

Then provide:
- Overall dimension score (0.0-1.0)
- Overall confidence in this dimension evaluation (0.0-1.0)
- Reasoning for the score

Be metacognitive: explicitly note what information you have, what's missing, and how that affects your confidence.

Return a JSON object with this structure:
{{
  "score": 0.85,
  "confidence": 0.9,
  "found_indicators": [
    {{
      "indicator": "indicator name",
      "evidence": "specific evidence from repo",
      "location": "where found (README, file structure, etc)",
      "confidence": 0.9
    }}
  ],
  "missing_indicators": ["indicator1", "indicator2"],
  "reasoning": "explanation of score and confidence"
}}

Be precise and trace all claims to specific evidence."""

        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )

        # Parse response
        response_text = response.content[0].text
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}") + 1
        json_text = response_text[start_idx:end_idx]
        data = json.loads(json_text)

        # Convert to DimensionScore
        found_indicators = [
            IndicatorEvidence(
                indicator=ind["indicator"],
                evidence=ind["evidence"],
                location=ind["location"],
                confidence=ind.get("confidence", 0.5),
            )
            for ind in data.get("found_indicators", [])
        ]

        return DimensionScore(
            dimension=dimension.name,
            score=data["score"],
            confidence=data["confidence"],
            found_indicators=found_indicators,
            missing_indicators=data.get("missing_indicators", []),
            reasoning=data["reasoning"],
        )

    def _generate_metacognitive_notes(
        self,
        dimension_scores: list[DimensionScore],
        context: RepositoryContext,
        overall_confidence: float,
    ) -> MetacognitiveNotes:
        """Generate metacognitive notes about the evaluation.

        Args:
            dimension_scores: All dimension scores
            context: Repository context
            overall_confidence: Overall evaluation confidence

        Returns:
            MetacognitiveNotes with reflection on evaluation quality
        """
        limitations = []

        # Check for missing context
        if not context.readme_content:
            limitations.append("No README available - limited documentation context")

        if not context.additional_files:
            limitations.append("No additional documentation files found")

        # Check for low confidence dimensions
        low_confidence_dims = [ds for ds in dimension_scores if ds.confidence < 0.5]
        if low_confidence_dims:
            for dim in low_confidence_dims:
                limitations.append(
                    f"Low confidence in {dim.dimension} - limited evidence available"
                )

        # Calculate context completeness
        has_readme = 1.0 if context.readme_content else 0.0
        has_structure = 1.0 if context.file_structure else 0.0
        has_additional = min(len(context.additional_files) / 3.0, 1.0)
        context_completeness = (has_readme + has_structure + has_additional) / 3.0

        # Identify confidence factors
        high_confidence_factors = []
        low_confidence_factors = []

        if context.readme_content and len(context.readme_content) > 500:
            high_confidence_factors.append("Comprehensive README")

        if context.file_structure and len(context.file_structure) > 5:
            high_confidence_factors.append("Clear project structure")

        if context.additional_files:
            high_confidence_factors.append("Additional documentation available")

        if overall_confidence < 0.6:
            low_confidence_factors.append("Limited contextual information")

        if not context.metadata.license_name:
            low_confidence_factors.append("No license information")

        return MetacognitiveNotes(
            context_completeness=round(context_completeness, 2),
            limitations=limitations,
            confidence_factors={"high": high_confidence_factors, "low": low_confidence_factors},
        )

    def _determine_recommendation(
        self,
        overall_relevance: float,
        overall_confidence: float,
        dimension_scores: list[DimensionScore],
    ) -> str:
        """Determine recommendation based on scores and confidence."""
        if overall_relevance >= 0.7 and overall_confidence >= 0.6:
            return "include"
        elif overall_relevance >= 0.5 and overall_confidence >= 0.5:
            return "include_with_notes"
        elif overall_confidence < 0.4:
            return "needs_review"
        else:
            return "exclude"

    def _generate_notes(
        self,
        dimension_scores: list[DimensionScore],
        overall_relevance: float,
        overall_confidence: float,
    ) -> str:
        """Generate human-readable notes about the evaluation."""
        notes_parts = []

        # Highlight strong dimensions
        strong_dims = [ds for ds in dimension_scores if ds.score >= 0.7]
        if strong_dims:
            strong_names = ", ".join([ds.dimension for ds in strong_dims])
            notes_parts.append(f"Strong in: {strong_names}")

        # Note weak dimensions
        weak_dims = [ds for ds in dimension_scores if ds.score < 0.5]
        if weak_dims:
            weak_names = ", ".join([ds.dimension for ds in weak_dims])
            notes_parts.append(f"Weak in: {weak_names}")

        # Note confidence issues
        if overall_confidence < 0.6:
            notes_parts.append("Evaluation confidence is moderate - additional review recommended")

        return ". ".join(notes_parts) if notes_parts else "No special notes"
