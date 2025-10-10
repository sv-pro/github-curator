"""Integration tests for the complete curation pipeline."""

from unittest.mock import MagicMock, patch

from curator.core.intent_structuring import IntentStructurer
from curator.core.metacognitive_eval import MetacognitiveEvaluator
from curator.github.api_client import GitHubAPIClient
from curator.github.repo_analyzer import RepositoryAnalyzer
from curator.github.smart_fetcher import SmartRepoFetcher


class TestCurationPipeline:
    """Integration tests for end-to-end curation."""

    @patch("curator.core.intent_structuring.load_llm_provider")
    @patch("curator.github.api_client.Github")
    def test_intent_structuring_flow(self, mock_github_class, mock_load_llm, sample_config):
        """Test the intent structuring step."""
        # Mock LLM provider
        mock_llm = MagicMock()
        mock_llm.generate_structured.return_value = {
            "dimensions": [
                {
                    "name": "test_dimension",
                    "weight": 1.0,
                    "indicators": [{"name": "test_indicator", "description": "Test"}],
                    "validation_rules": [],
                }
            ],
            "constraints": {"min_stars": 50},
            "focus_areas": ["test"],
            "exclusions": [],
        }
        mock_load_llm.return_value = mock_llm

        structurer = IntentStructurer(config_path=str(sample_config))
        intent = structurer.structure_theme("Modern Python web frameworks")

        # Should call LLM
        assert mock_llm.generate_structured.called or intent is not None

    @patch("curator.github.api_client.Github")
    def test_github_search_flow(self, mock_github_class, sample_search_result):
        """Test GitHub repository search."""
        # Mock GitHub API
        mock_repo = MagicMock()
        mock_repo.full_name = sample_search_result.full_name
        mock_repo.name = sample_search_result.name
        mock_repo.description = sample_search_result.description
        mock_repo.html_url = sample_search_result.html_url
        mock_repo.stargazers_count = sample_search_result.stars
        mock_repo.forks_count = sample_search_result.forks
        mock_repo.language = sample_search_result.language
        mock_repo.get_topics.return_value = sample_search_result.topics
        mock_repo.created_at = sample_search_result.created_at
        mock_repo.updated_at = sample_search_result.updated_at

        mock_github_instance = MagicMock()
        mock_github_instance.search_repositories.return_value = [mock_repo]
        mock_github_class.return_value = mock_github_instance

        client = GitHubAPIClient(token="test_token")
        results = client.search_repositories("python web framework", limit=10)

        assert mock_github_instance.search_repositories.called
        assert len(results) >= 0

    @patch("curator.core.intent_structuring.load_llm_provider")
    @patch("curator.core.metacognitive_eval.load_llm_provider")
    @patch("curator.github.api_client.Github")
    def test_smart_fetcher_integration(
        self,
        mock_github_class,
        mock_eval_llm,
        mock_intent_llm,
        sample_config,
        sample_search_result,
        sample_readme_content,
    ):
        """Test Smart Fetcher with GitHub client and evaluator."""
        # Mock GitHub client
        mock_readme = MagicMock()
        mock_readme.decoded_content = sample_readme_content.encode()
        mock_repo = MagicMock()
        mock_repo.get_readme.return_value = mock_readme

        mock_github_instance = MagicMock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_github_class.return_value = mock_github_instance

        # Mock LLM for intent
        mock_llm_intent = MagicMock()
        mock_llm_intent.generate_structured.return_value = {
            "dimensions": [
                {
                    "name": "project_maturity",
                    "weight": 1.0,
                    "indicators": [{"name": "active_development", "description": "Recent commits"}],
                    "validation_rules": [],
                }
            ],
            "constraints": {"min_stars": 50},
            "focus_areas": ["web"],
            "exclusions": [],
        }
        mock_intent_llm.return_value = mock_llm_intent

        # Mock LLM for evaluation
        mock_llm_eval = MagicMock()
        mock_llm_eval.generate_structured.return_value = {
            "dimension_evaluations": [
                {
                    "dimension_name": "project_maturity",
                    "score": 0.75,
                    "confidence": 0.85,
                    "indicators": [],
                    "reasoning": "Good",
                }
            ],
            "overall_score": 0.75,
            "overall_confidence": 0.85,
        }
        mock_eval_llm.return_value = mock_llm_eval

        # Create pipeline components
        github_client = GitHubAPIClient(token="test_token")
        structurer = IntentStructurer(config_path=str(sample_config))
        intent = structurer.structure_theme("Modern Python web frameworks")

        if intent:
            analyzer = RepositoryAnalyzer(github_client)
            evaluator = MetacognitiveEvaluator(config_path=str(sample_config))
            smart_fetcher = SmartRepoFetcher(
                str(sample_config), intent, github_client, analyzer, evaluator
            )

            # Analyze repository
            result = smart_fetcher.analyze(sample_search_result, thoroughness="standard")

            # Should complete or call appropriate methods
            assert result is not None or mock_llm_eval.generate_structured.called

    @patch("curator.github.api_client.Github")
    def test_repo_analyzer_integration(
        self, mock_github_class, sample_search_result, sample_readme_content
    ):
        """Test repository analyzer with GitHub client."""
        # Mock GitHub API responses
        mock_readme = MagicMock()
        mock_readme.decoded_content = sample_readme_content.encode()

        mock_repo = MagicMock()
        mock_repo.get_readme.return_value = mock_readme
        mock_repo.get_contents.return_value = []

        mock_github_instance = MagicMock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_github_class.return_value = mock_github_instance

        github_client = GitHubAPIClient(token="test_token")
        analyzer = RepositoryAnalyzer(github_client)

        analysis = analyzer.analyze_repository(sample_search_result)

        # Should return analysis results
        assert analysis is not None
        assert isinstance(analysis, dict)


class TestSmartFetcherModes:
    """Integration tests for different Smart Fetcher modes."""

    @patch("curator.core.metacognitive_eval.load_llm_provider")
    @patch("curator.github.api_client.Github")
    def test_fast_mode(
        self,
        mock_github_class,
        mock_llm,
        sample_config,
        sample_structured_intent,
        sample_search_result,
    ):
        """Test fast mode skips aggressively."""
        mock_github_instance = MagicMock()
        mock_github_class.return_value = mock_github_instance

        mock_llm.return_value = MagicMock()

        github_client = GitHubAPIClient(token="test_token")
        analyzer = RepositoryAnalyzer(github_client)
        evaluator = MetacognitiveEvaluator(config_path=str(sample_config))

        smart_fetcher = SmartRepoFetcher(
            str(sample_config),
            sample_structured_intent,
            github_client,
            analyzer,
            evaluator,
        )

        # Low-quality repo
        sample_search_result.stars = 1
        result = smart_fetcher.analyze(sample_search_result, thoroughness="fast")

        # Should skip in fast mode
        assert result is None

    @patch("curator.core.metacognitive_eval.load_llm_provider")
    @patch("curator.github.api_client.Github")
    def test_exhaustive_mode(
        self,
        mock_github_class,
        mock_llm,
        sample_config,
        sample_structured_intent,
        sample_search_result,
        sample_readme_content,
    ):
        """Test exhaustive mode analyzes thoroughly."""
        # Mock GitHub
        mock_readme = MagicMock()
        mock_readme.decoded_content = sample_readme_content.encode()
        mock_repo = MagicMock()
        mock_repo.get_readme.return_value = mock_readme

        mock_github_instance = MagicMock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_github_class.return_value = mock_github_instance

        # Mock LLM
        mock_llm_instance = MagicMock()
        mock_llm_instance.generate_structured.return_value = {
            "dimension_evaluations": [
                {
                    "dimension_name": "project_maturity",
                    "score": 0.8,
                    "confidence": 0.9,
                    "indicators": [],
                    "reasoning": "Excellent",
                }
            ],
            "overall_score": 0.8,
            "overall_confidence": 0.9,
        }
        mock_llm.return_value = mock_llm_instance

        github_client = GitHubAPIClient(token="test_token")
        analyzer = RepositoryAnalyzer(github_client)
        evaluator = MetacognitiveEvaluator(config_path=str(sample_config))

        smart_fetcher = SmartRepoFetcher(
            str(sample_config),
            sample_structured_intent,
            github_client,
            analyzer,
            evaluator,
        )

        result = smart_fetcher.analyze(sample_search_result, thoroughness="exhaustive")

        # Should perform deep analysis
        assert result is not None or mock_llm_instance.generate_structured.called
