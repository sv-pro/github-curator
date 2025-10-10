"""Pytest configuration and shared fixtures."""

import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
import yaml

from curator.core.intent_structuring import (
    Constraints,
    Dimension,
    Indicator,
    StructuredIntent,
)
from curator.github.api_client import SearchResult


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_config(temp_dir: Path) -> Path:
    """Create a sample configuration file."""
    config = {
        "github": {
            "token": "test_token",
            "search_limit": 10,
            "rate_limit_pause": 60,
        },
        "llm": {
            "provider": "anthropic",
            "model": "claude-3-5-sonnet-20241022",
            "temperature": 0.7,
            "max_tokens": 4000,
        },
        "intent_structuring": {
            "max_dimensions": 5,
            "min_dimension_weight": 0.1,
        },
        "evaluation": {
            "min_confidence": 0.3,
            "min_indicators_per_dimension": 2,
        },
        "smart_fetch": {
            "enabled": True,
            "enable_metadata_filter": True,
            "min_stars_multiplier": 0.5,
            "max_size_kb": 500000,
            "min_size_kb": 50,
            "enable_quick_llm": False,
            "quick_model": "claude-3-haiku-20240307",
            "min_quick_score": 0.3,
            "high_promise_score": 0.7,
            "readme_max_lines": 500,
            "clone_threshold_score": 0.8,
            "clone_threshold_confidence": 0.6,
        },
    }
    config_path = temp_dir / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    return config_path


@pytest.fixture
def sample_structured_intent() -> StructuredIntent:
    """Create a sample structured intent for testing."""
    indicators = [
        Indicator(name="active_development", description="Recent commits"),
        Indicator(name="good_documentation", description="README and docs"),
        Indicator(name="community_engagement", description="Issues and PRs"),
    ]
    dimension = Dimension(
        name="project_maturity",
        weight=1.0,
        indicators=indicators,
        validation_rules=["must have >2 indicators"],
    )
    constraints = Constraints(min_stars=50, max_age_months=12, requires_license=True)

    return StructuredIntent(
        intent_id="test-intent-123",
        theme="Modern Python web frameworks",
        dimensions=[dimension],
        constraints=constraints,
        focus_areas=["web", "framework", "python"],
        exclusions=["deprecated", "archived"],
    )


@pytest.fixture
def sample_search_result() -> SearchResult:
    """Create a sample GitHub search result."""
    return SearchResult(
        full_name="test-org/test-repo",
        name="test-repo",
        owner="test-org",
        description="A test repository for modern Python web development",
        stars=150,
        last_updated=datetime.now(),
        language="Python",
        license_name="MIT",
        url="https://github.com/test-org/test-repo",
        topics=["web", "framework", "python", "async"],
    )


@pytest.fixture
def mock_github_client():
    """Create a mock GitHub API client."""
    client = MagicMock()
    client.search_repositories.return_value = []
    client.get_repository.return_value = None
    client.get_readme_content.return_value = "# Test Repository\n\nA test repository."
    client.get_file_content.return_value = "# Sample file content"
    return client


@pytest.fixture
def mock_llm_provider():
    """Create a mock LLM provider."""
    provider = MagicMock()
    provider.generate.return_value = "Mock LLM response"
    provider.generate_structured.return_value = {"mock": "structured response"}
    return provider


@pytest.fixture
def mock_repo_analyzer():
    """Create a mock repository analyzer."""
    analyzer = MagicMock()
    analyzer.analyze.return_value = {
        "readme_length": 1000,
        "has_tests": True,
        "has_ci": True,
        "file_count": 50,
    }
    return analyzer


@pytest.fixture
def mock_evaluator():
    """Create a mock metacognitive evaluator."""
    evaluator = MagicMock()
    evaluator.evaluate.return_value = None  # Returns EvaluationReport
    return evaluator


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Mock environment variables for all tests."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
    monkeypatch.setenv("GITHUB_TOKEN", "test-github-token")


@pytest.fixture
def sample_readme_content() -> str:
    """Sample README content for testing."""
    return """# Test Repository

A modern Python web framework for building APIs.

## Features

- Fast and efficient
- Easy to use
- Well documented
- Active community

## Installation

```bash
pip install test-repo
```

## Usage

```python
from test_repo import App

app = App()
app.run()
```

## Contributing

We welcome contributions! Please see CONTRIBUTING.md.

## License

MIT License
"""


@pytest.fixture
def sample_repo_metadata() -> dict[str, Any]:
    """Sample repository metadata."""
    return {
        "full_name": "test-org/test-repo",
        "stars": 150,
        "forks": 25,
        "language": "Python",
        "topics": ["web", "framework", "python"],
        "created_at": "2023-01-15T10:00:00Z",
        "updated_at": "2024-10-01T15:30:00Z",
        "license": "MIT",
        "size_kb": 1500,
        "open_issues": 5,
        "has_wiki": True,
    }
