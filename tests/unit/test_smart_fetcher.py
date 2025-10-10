"""Unit tests for Smart Repo Fetcher."""

from unittest.mock import MagicMock

from curator.github.smart_fetcher import (
    AnalysisTrace,
    Decision,
    SmartRepoFetcher,
    StageResult,
)


class TestSmartRepoFetcher:
    """Test suite for SmartRepoFetcher class."""

    def test_stage1_metadata_check_high_stars(
        self,
        sample_config,
        sample_structured_intent,
        mock_github_client,
        mock_repo_analyzer,
        mock_evaluator,
        sample_search_result,
    ):
        """Test Stage 1 accepts repo with high stars."""
        fetcher = SmartRepoFetcher(
            str(sample_config),
            sample_structured_intent,
            mock_github_client,
            mock_repo_analyzer,
            mock_evaluator,
        )

        # High stars repo
        sample_search_result.stars = 1000
        result = fetcher.stage1_metadata_check(sample_search_result)

        assert result.decision == Decision.CONTINUE_STANDARD
        assert result.confidence > 0.5

    def test_stage1_metadata_check_low_stars(
        self,
        sample_config,
        sample_structured_intent,
        mock_github_client,
        mock_repo_analyzer,
        mock_evaluator,
        sample_search_result,
    ):
        """Test Stage 1 skips repo with very low stars."""
        fetcher = SmartRepoFetcher(
            str(sample_config),
            sample_structured_intent,
            mock_github_client,
            mock_repo_analyzer,
            mock_evaluator,
        )

        # Very low stars
        sample_search_result.stars = 1
        result = fetcher.stage1_metadata_check(sample_search_result)

        # Should likely be skipped or have low confidence
        assert result.confidence <= 0.7

    def test_stage1_metadata_check_matching_topics(
        self,
        sample_config,
        sample_structured_intent,
        mock_github_client,
        mock_repo_analyzer,
        mock_evaluator,
        sample_search_result,
    ):
        """Test Stage 1 rewards matching topics."""
        fetcher = SmartRepoFetcher(
            str(sample_config),
            sample_structured_intent,
            mock_github_client,
            mock_repo_analyzer,
            mock_evaluator,
        )

        # Add focus area topics
        sample_search_result.topics = ["web", "framework", "python"]
        result = fetcher.stage1_metadata_check(sample_search_result)

        assert result.decision == Decision.CONTINUE_STANDARD
        assert result.confidence > 0.5

    def test_stage2_lightweight_analysis(
        self,
        sample_config,
        sample_structured_intent,
        mock_github_client,
        mock_repo_analyzer,
        mock_evaluator,
        sample_search_result,
        sample_readme_content,
    ):
        """Test Stage 2 lightweight README analysis."""
        mock_github_client.get_readme_content.return_value = sample_readme_content

        fetcher = SmartRepoFetcher(
            str(sample_config),
            sample_structured_intent,
            mock_github_client,
            mock_repo_analyzer,
            mock_evaluator,
        )

        result = fetcher.stage2_lightweight_analysis(sample_search_result)

        # Should call GitHub client
        mock_github_client.get_readme_content.assert_called_once()

        # Should return a decision
        assert result.decision in [
            Decision.SKIP,
            Decision.CONTINUE_STANDARD,
            Decision.CONTINUE_DEEP,
        ]
        assert 0.0 <= result.confidence <= 1.0

    def test_stage2_no_readme(
        self,
        sample_config,
        sample_structured_intent,
        mock_github_client,
        mock_repo_analyzer,
        mock_evaluator,
        sample_search_result,
    ):
        """Test Stage 2 handles missing README."""
        mock_github_client.get_readme_content.return_value = None

        fetcher = SmartRepoFetcher(
            str(sample_config),
            sample_structured_intent,
            mock_github_client,
            mock_repo_analyzer,
            mock_evaluator,
        )

        result = fetcher.stage2_lightweight_analysis(sample_search_result)

        # Should still return a result (likely skip)
        assert result.decision is not None
        assert result.confidence >= 0.0

    def test_stage3_deep_analysis(
        self,
        sample_config,
        sample_structured_intent,
        mock_github_client,
        mock_repo_analyzer,
        mock_evaluator,
        sample_search_result,
    ):
        """Test Stage 3 calls full evaluation."""
        # Mock evaluator to return a proper evaluation
        mock_evaluation = MagicMock()
        mock_evaluation.overall_score = 0.75
        mock_evaluation.overall_confidence = 0.85
        mock_evaluator.evaluate.return_value = mock_evaluation

        fetcher = SmartRepoFetcher(
            str(sample_config),
            sample_structured_intent,
            mock_github_client,
            mock_repo_analyzer,
            mock_evaluator,
        )

        result = fetcher.stage3_deep_analysis(sample_search_result)

        # Should call evaluator
        mock_evaluator.evaluate.assert_called_once()

        # Should return continue decision for good score
        assert result.decision == Decision.CONTINUE_STANDARD
        assert result.confidence > 0.5

    def test_analyze_fast_mode_skip_early(
        self,
        sample_config,
        sample_structured_intent,
        mock_github_client,
        mock_repo_analyzer,
        mock_evaluator,
        sample_search_result,
    ):
        """Test fast mode skips early when appropriate."""
        fetcher = SmartRepoFetcher(
            str(sample_config),
            sample_structured_intent,
            mock_github_client,
            mock_repo_analyzer,
            mock_evaluator,
        )

        # Low stars - should skip in fast mode
        sample_search_result.stars = 1
        result = fetcher.analyze(sample_search_result, thoroughness="fast")

        # Should skip
        assert result is None

    def test_analyze_exhaustive_mode_runs_all_stages(
        self,
        sample_config,
        sample_structured_intent,
        mock_github_client,
        mock_repo_analyzer,
        mock_evaluator,
        sample_search_result,
        sample_readme_content,
    ):
        """Test exhaustive mode runs through all stages."""
        mock_github_client.get_readme_content.return_value = sample_readme_content
        mock_evaluation = MagicMock()
        mock_evaluation.overall_score = 0.85
        mock_evaluation.overall_confidence = 0.9
        mock_evaluator.evaluate.return_value = mock_evaluation

        fetcher = SmartRepoFetcher(
            str(sample_config),
            sample_structured_intent,
            mock_github_client,
            mock_repo_analyzer,
            mock_evaluator,
        )

        result = fetcher.analyze(sample_search_result, thoroughness="exhaustive")

        # Should complete analysis
        assert result is not None or mock_evaluator.evaluate.called

    def test_get_savings_summary(
        self,
        sample_config,
        sample_structured_intent,
        mock_github_client,
        mock_repo_analyzer,
        mock_evaluator,
        sample_search_result,
    ):
        """Test savings summary calculation."""
        fetcher = SmartRepoFetcher(
            str(sample_config),
            sample_structured_intent,
            mock_github_client,
            mock_repo_analyzer,
            mock_evaluator,
        )

        # Analyze a few repos
        sample_search_result.stars = 1
        fetcher.analyze(sample_search_result, thoroughness="fast")  # Should skip

        sample_search_result.stars = 1000
        fetcher.analyze(sample_search_result, thoroughness="fast")  # Should analyze

        summary = fetcher.get_savings_summary()

        assert "analyzed_count" in summary
        assert "skipped_count" in summary
        assert "skip_rate" in summary
        assert summary["analyzed_count"] + summary["skipped_count"] == 2


class TestDecision:
    """Test Decision enum."""

    def test_decision_values(self):
        """Test Decision enum has correct values."""
        assert Decision.SKIP.value == "skip"
        assert Decision.CONTINUE_STANDARD.value == "continue"
        assert Decision.CONTINUE_DEEP.value == "continue_deep"


class TestStageResult:
    """Test StageResult dataclass."""

    def test_stage_result_creation(self):
        """Test creating a StageResult."""
        result = StageResult(
            decision=Decision.CONTINUE_STANDARD,
            confidence=0.75,
            reasoning="Good indicators",
            cost_saved=0.5,
            data_fetched={"readme": "content"},
        )

        assert result.decision == Decision.CONTINUE_STANDARD
        assert result.confidence == 0.75
        assert result.reasoning == "Good indicators"
        assert result.cost_saved == 0.5
        assert result.data_fetched["readme"] == "content"


class TestAnalysisTrace:
    """Test AnalysisTrace dataclass."""

    def test_analysis_trace_creation(self):
        """Test creating an AnalysisTrace."""
        trace = AnalysisTrace(
            repo="test-org/test-repo",
            thoroughness="standard",
        )

        assert trace.repo == "test-org/test-repo"
        assert trace.thoroughness == "standard"
        assert len(trace.stages) == 0
        assert trace.fast_tracked is False

    def test_analysis_trace_with_stages(self):
        """Test AnalysisTrace with stage results."""
        stage1 = StageResult(
            decision=Decision.CONTINUE_STANDARD,
            confidence=0.6,
            reasoning="Metadata looks good",
            cost_saved=0.0,
        )
        stage2 = StageResult(
            decision=Decision.SKIP,
            confidence=0.3,
            reasoning="README not relevant",
            cost_saved=0.8,
        )

        trace = AnalysisTrace(
            repo="test-org/test-repo",
            thoroughness="fast",
            stages=[stage1, stage2],
        )

        assert len(trace.stages) == 2
        assert trace.stages[0].decision == Decision.CONTINUE_STANDARD
        assert trace.stages[1].decision == Decision.SKIP
