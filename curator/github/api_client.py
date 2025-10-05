"""GitHub API client with rate limiting."""

import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

import yaml
from github import Github, GithubException, Repository


@dataclass
class SearchResult:
    """GitHub repository search result."""

    full_name: str
    name: str
    owner: str
    description: str
    stars: int
    last_updated: datetime
    language: str
    license_name: Optional[str]
    url: str
    topics: list[str]


class GitHubAPIClient:
    """GitHub API client with rate limiting and search capabilities."""

    def __init__(self, config_path: str = "config/curator.yaml", token: Optional[str] = None):
        """Initialize GitHub client.

        Args:
            config_path: Path to configuration file
            token: GitHub API token (if not provided, uses GITHUB_TOKEN env var)
        """
        self.config = self._load_config(config_path)
        api_token = token or os.getenv("GITHUB_TOKEN")
        if not api_token:
            raise ValueError("GitHub token required. Set GITHUB_TOKEN environment variable.")

        self.client = Github(api_token)
        self.rate_limit_buffer = self.config["github"]["rate_limit_buffer"]
        self.search_limit = self.config["github"]["search_limit"]

    def _load_config(self, config_path: str) -> dict[str, Any]:
        """Load configuration from YAML file."""
        with open(config_path) as f:
            return yaml.safe_load(f)

    def _check_rate_limit(self):
        """Check rate limit and sleep if necessary."""
        rate_limit = self.client.get_rate_limit()
        remaining = rate_limit.resources.core.remaining

        if remaining < self.rate_limit_buffer:
            reset_time = rate_limit.resources.core.reset
            sleep_time = (reset_time - datetime.now()).total_seconds() + 10
            if sleep_time > 0:
                print(f"Rate limit approaching. Sleeping for {sleep_time:.0f} seconds...")
                time.sleep(sleep_time)

    def search_repositories(
        self,
        query: str,
        min_stars: int = 50,
        max_age_months: int = 6,
        requires_license: bool = True,
        language: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[SearchResult]:
        """Search for repositories matching criteria.

        Args:
            query: Search query string
            min_stars: Minimum number of stars
            max_age_months: Maximum age in months since last update
            requires_license: Whether license is required
            language: Filter by programming language
            limit: Maximum number of results

        Returns:
            List of SearchResult objects
        """
        self._check_rate_limit()

        # Build search query
        query_parts = [query]
        query_parts.append(f"stars:>={min_stars}")

        # Calculate date for max_age_months
        cutoff_date = datetime.now() - timedelta(days=max_age_months * 30)
        query_parts.append(f"pushed:>={cutoff_date.strftime('%Y-%m-%d')}")

        # Note: GitHub doesn't support license:* wildcard
        # We'll filter repositories without licenses in post-processing if needed
        # For now, we skip the license filter in the search query

        if language:
            query_parts.append(f"language:{language}")

        full_query = " ".join(query_parts)
        print(f"  Query: {full_query}")

        # Execute search
        try:
            search_limit = limit or self.search_limit
            repositories = self.client.search_repositories(
                query=full_query, sort="stars", order="desc"
            )

            print(f"  Total matches: {repositories.totalCount}")

            results = []
            count = 0
            for repo in repositories:
                if count >= search_limit:
                    break

                self._check_rate_limit()

                # Filter by license if required
                if requires_license and not repo.license:
                    print(f"  ⊘ Skipping {repo.full_name} - no license")
                    continue

                print(f"  ✓ Found: {repo.full_name} (⭐ {repo.stargazers_count})")
                results.append(
                    SearchResult(
                        full_name=repo.full_name,
                        name=repo.name,
                        owner=repo.owner.login,
                        description=repo.description or "",
                        stars=repo.stargazers_count,
                        last_updated=repo.pushed_at,
                        language=repo.language or "Unknown",
                        license_name=repo.license.name if repo.license else None,
                        url=repo.html_url,
                        topics=repo.get_topics(),
                    )
                )
                count += 1

            print(f"  Selected {len(results)} repositories for evaluation")
            return results

        except GithubException as e:
            print(f"GitHub API error: {e}")
            raise

    def get_repository(self, full_name: str) -> Repository.Repository:
        """Get repository object by full name.

        Args:
            full_name: Repository full name (owner/repo)

        Returns:
            GitHub Repository object
        """
        self._check_rate_limit()
        return self.client.get_repo(full_name)

    def get_readme_content(self, full_name: str) -> Optional[str]:
        """Get README content for a repository.

        Args:
            full_name: Repository full name (owner/repo)

        Returns:
            README content as string, or None if not found
        """
        self._check_rate_limit()

        try:
            repo = self.get_repository(full_name)
            readme = repo.get_readme()
            return readme.decoded_content.decode("utf-8")
        except GithubException:
            return None

    def get_file_content(self, full_name: str, file_path: str) -> Optional[str]:
        """Get content of a specific file.

        Args:
            full_name: Repository full name (owner/repo)
            file_path: Path to file in repository

        Returns:
            File content as string, or None if not found
        """
        self._check_rate_limit()

        try:
            repo = self.get_repository(full_name)
            content = repo.get_contents(file_path)
            if isinstance(content, list):
                return None  # It's a directory
            return content.decoded_content.decode("utf-8")
        except GithubException:
            return None

    def list_directory(self, full_name: str, path: str = "") -> list[str]:
        """List contents of a directory.

        Args:
            full_name: Repository full name (owner/repo)
            path: Directory path (empty for root)

        Returns:
            List of file/directory names
        """
        self._check_rate_limit()

        try:
            repo = self.get_repository(full_name)
            contents = repo.get_contents(path)
            if isinstance(contents, list):
                return [item.name for item in contents]
            return [contents.name]
        except GithubException:
            return []

    def get_repository_structure(self, full_name: str, max_depth: int = 2) -> dict[str, Any]:
        """Get repository directory structure.

        Args:
            full_name: Repository full name (owner/repo)
            max_depth: Maximum depth to traverse

        Returns:
            Nested dictionary representing file structure
        """
        self._check_rate_limit()

        def _get_structure(path: str, depth: int) -> dict[str, Any]:
            if depth >= max_depth:
                return {}

            structure: dict[str, Any] = {}
            items = self.list_directory(full_name, path)

            for item in items:
                item_path = f"{path}/{item}" if path else item
                # Try to get as directory
                sub_items = self.list_directory(full_name, item_path)
                if sub_items and sub_items != [item]:
                    print(f"      📁 {item_path}/")
                    structure[item] = _get_structure(item_path, depth + 1)
                else:
                    print(f"      📄 {item_path}")
                    structure[item] = "file"  # type: ignore[assignment]

            return structure

        try:
            return _get_structure("", 0)
        except GithubException as e:
            print(f"Error getting structure: {e}")
            return {}
