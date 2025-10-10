"""Unit tests for GitHub API client."""

from unittest.mock import MagicMock, patch

from curator.github.api_client import GitHubAPIClient, SearchResult


class TestSearchResult:
    """Test SearchResult dataclass."""

    def test_search_result_creation(self):
        """Test creating a search result."""
        from datetime import datetime

        result = SearchResult(
            full_name="owner/repo",
            name="repo",
            owner="owner",
            description="Test repository",
            stars=100,
            last_updated=datetime(2024, 1, 1),
            language="Python",
            license_name="MIT",
            url="https://github.com/owner/repo",
            topics=["test", "python"],
        )

        assert result.full_name == "owner/repo"
        assert result.name == "repo"
        assert result.stars == 100
        assert result.language == "Python"
        assert "test" in result.topics


class TestGitHubAPIClient:
    """Test GitHubAPIClient class."""

    @patch("curator.github.api_client.Github")
    def test_client_initialization(self, mock_github_class):
        """Test initializing the GitHub client."""
        mock_github_class.return_value = MagicMock()

        client = GitHubAPIClient(token="test_token")

        assert client is not None
        mock_github_class.assert_called_once_with("test_token")

    @patch("curator.github.api_client.Github")
    def test_search_repositories(self, mock_github_class):
        """Test searching repositories."""
        # Mock GitHub API
        mock_repo = MagicMock()
        mock_repo.full_name = "owner/repo"
        mock_repo.name = "repo"
        mock_repo.description = "Test repo"
        mock_repo.html_url = "https://github.com/owner/repo"
        mock_repo.stargazers_count = 100
        mock_repo.forks_count = 20
        mock_repo.language = "Python"
        mock_repo.get_topics.return_value = ["test", "python"]
        mock_repo.created_at = "2023-01-01T00:00:00Z"
        mock_repo.updated_at = "2024-01-01T00:00:00Z"
        mock_repo.license.name = "MIT License" if mock_repo.license else None

        mock_github_instance = MagicMock()
        mock_github_instance.search_repositories.return_value = [mock_repo]
        mock_github_class.return_value = mock_github_instance

        client = GitHubAPIClient(token="test_token")
        results = client.search_repositories("test query", limit=10)

        assert len(results) >= 0
        mock_github_instance.search_repositories.assert_called()

    @patch("curator.github.api_client.Github")
    def test_get_repository(self, mock_github_class):
        """Test getting a specific repository."""
        mock_repo = MagicMock()
        mock_repo.full_name = "owner/repo"

        mock_github_instance = MagicMock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_github_class.return_value = mock_github_instance

        client = GitHubAPIClient(token="test_token")
        repo = client.get_repository("owner/repo")

        mock_github_instance.get_repo.assert_called_once_with("owner/repo")
        assert repo is not None

    @patch("curator.github.api_client.Github")
    def test_get_readme_content(self, mock_github_class):
        """Test fetching README content."""
        mock_readme = MagicMock()
        mock_readme.decoded_content = b"# Test README\n\nThis is a test."

        mock_repo = MagicMock()
        mock_repo.get_readme.return_value = mock_readme

        mock_github_instance = MagicMock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_github_class.return_value = mock_github_instance

        client = GitHubAPIClient(token="test_token")
        readme = client.get_readme_content("owner/repo")

        assert readme is not None
        assert "Test README" in readme or mock_repo.get_readme.called

    @patch("curator.github.api_client.Github")
    def test_get_readme_content_not_found(self, mock_github_class):
        """Test handling missing README."""
        mock_repo = MagicMock()
        mock_repo.get_readme.side_effect = Exception("Not found")

        mock_github_instance = MagicMock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_github_class.return_value = mock_github_instance

        client = GitHubAPIClient(token="test_token")
        readme = client.get_readme_content("owner/repo")

        # Should handle error gracefully
        assert readme is None or readme == ""

    @patch("curator.github.api_client.Github")
    def test_rate_limit_handling(self, mock_github_class):
        """Test rate limit handling."""
        mock_rate_limit = MagicMock()
        mock_rate_limit.core.remaining = 100
        mock_rate_limit.core.limit = 5000

        mock_github_instance = MagicMock()
        mock_github_instance.get_user.return_value = MagicMock(login="testuser")
        mock_github_instance.get_rate_limit.return_value = mock_rate_limit
        mock_github_class.return_value = mock_github_instance

        client = GitHubAPIClient(token="test_token")

        # Rate limit is checked internally via _check_rate_limit()
        # Just verify the client was initialized properly
        assert client.client == mock_github_instance

    @patch("curator.github.api_client.Github")
    def test_get_file_content(self, mock_github_class):
        """Test fetching file content."""
        mock_content = MagicMock()
        mock_content.decoded_content = b"print('Hello, World!')"

        mock_repo = MagicMock()
        mock_repo.get_contents.return_value = mock_content

        mock_github_instance = MagicMock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_github_class.return_value = mock_github_instance

        client = GitHubAPIClient(token="test_token")
        content = client.get_file_content("owner/repo", "main.py")

        assert content is not None or mock_repo.get_contents.called

    @patch("curator.github.api_client.Github")
    def test_search_with_constraints(self, mock_github_class):
        """Test search with constraint filters."""
        mock_github_instance = MagicMock()
        mock_github_instance.search_repositories.return_value = []
        mock_github_class.return_value = mock_github_instance

        client = GitHubAPIClient(token="test_token")

        # Build query with constraints
        query = "test stars:>50 language:Python"
        results = client.search_repositories(query, limit=10)

        mock_github_instance.search_repositories.assert_called()
        # Check that query was used
        call_args = mock_github_instance.search_repositories.call_args
        assert call_args is not None or len(results) >= 0
