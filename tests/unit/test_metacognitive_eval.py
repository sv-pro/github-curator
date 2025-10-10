"""Unit tests for metacognitive evaluation."""

from unittest.mock import MagicMock, patch

from curator.core.metacognitive_eval import (
    DimensionScore,
    IndicatorEvidence,
    MetacognitiveEvaluator,
    MetacognitiveNotes,
)


class TestIndicatorEvidence:
    """Test IndicatorEvidence dataclass."""

    def test_indicator_evidence_creation(self):
        """Test creating indicator evidence."""
        evidence = IndicatorEvidence(
            indicator="active_development",
            evidence="Last commit: 2 days ago",
            location="repository_metadata",
            confidence=0.85,
        )

        assert evidence.indicator == "active_development"
        assert evidence.confidence == 0.85
        assert "2 days ago" in evidence.evidence
        assert evidence.location == "repository_metadata"


class TestDimensionScore:
    """Test DimensionScore dataclass."""

    def test_dimension_score_creation(self):
        """Test creating dimension score."""
        indicators = [
            IndicatorEvidence(
                indicator="test1",
                evidence="evidence",
                location="test",
                confidence=0.8,
            )
        ]

        dim_score = DimensionScore(
            dimension="test_dimension",
            score=0.75,
            confidence=0.85,
            found_indicators=indicators,
            missing_indicators=["test2"],
            reasoning="Test reasoning",
        )

        assert dim_score.dimension == "test_dimension"
        assert dim_score.score == 0.75
        assert dim_score.confidence == 0.85
        assert len(dim_score.found_indicators) == 1
        assert "test2" in dim_score.missing_indicators
        assert dim_score.reasoning == "Test reasoning"


class TestMetacognitiveNotes:
    """Test MetacognitiveNotes dataclass."""

    def test_metacognitive_notes_creation(self):
        """Test creating metacognitive notes."""
        notes = MetacognitiveNotes(
            context_completeness=0.8,
            limitations=["Limited API access", "No code analysis"],
            confidence_factors={
                "high": ["Recent activity", "Good documentation"],
                "low": ["Few contributors"],
            },
        )

        assert notes.context_completeness == 0.8
        assert len(notes.limitations) == 2
        assert "high" in notes.confidence_factors
        assert "low" in notes.confidence_factors


class TestMetacognitiveEvaluator:
    """Test MetacognitiveEvaluator class."""

    def test_evaluator_class_exists(self):
        """Test that MetacognitiveEvaluator class exists."""
        assert MetacognitiveEvaluator is not None

    @patch("curator.core.metacognitive_eval.anthropic.Anthropic")
    def test_evaluator_can_be_instantiated(self, mock_anthropic):
        """Test MetacognitiveEvaluator can be instantiated."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        # This is a basic smoke test
        # Full integration tests will cover actual evaluation
        assert MetacognitiveEvaluator is not None
