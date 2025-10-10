# Testing Guide

This document describes the testing strategy and practices for GitHub Curator.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Phase Gate Testing](#phase-gate-testing)
- [Writing Tests](#writing-tests)
- [CI/CD Integration](#cicd-integration)
- [Coverage Requirements](#coverage-requirements)

## Overview

GitHub Curator uses a comprehensive testing strategy to ensure code quality, reliability, and maintainability. The test suite includes:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions and end-to-end workflows
- **Phase Gate Tests**: Comprehensive quality gates between development phases
- **Linters**: Code quality and style checks (ruff, black, mypy)
- **Coverage Analysis**: Ensure adequate test coverage (minimum 70%)

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── __init__.py
├── unit/                    # Unit tests
│   ├── __init__.py
│   ├── test_smart_fetcher.py
│   ├── test_metacognitive_eval.py
│   ├── test_github_api_client.py
│   └── test_intent_structuring.py
├── integration/             # Integration tests
│   ├── __init__.py
│   └── test_curation_pipeline.py
└── fixtures/                # Test data and fixtures
    └── __init__.py
```

## Running Tests

### Quick Start

```bash
# Run all tests
make test

# Run with verbose output
make test-verbose

# Run only unit tests
make test-unit

# Run only integration tests
make test-integration

# Run with detailed coverage report
make test-coverage
```

### Using pytest directly

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_smart_fetcher.py

# Run specific test function
pytest tests/unit/test_smart_fetcher.py::TestSmartRepoFetcher::test_stage1_metadata_check_high_stars

# Run with coverage
pytest --cov=curator --cov-report=html

# Run tests matching a pattern
pytest -k "smart_fetcher"

# Run with verbose output
pytest -v

# Show print statements
pytest -s
```

## Phase Gate Testing

Phase gate tests ensure quality standards are met before progressing to the next development phase.

### Running Phase Gate Tests

```bash
# Run all phase gate tests
make test-phase-gate

# Run phase gate for specific phase (e.g., Phase 2)
make test-phase-gate PHASE=2

# Run in strict mode (80% coverage, fail on warnings)
make test-phase-gate-strict

# Using the script directly
python scripts/run_phase_gate_tests.py --phase 2
python scripts/run_phase_gate_tests.py --strict --coverage-min 80
python scripts/run_phase_gate_tests.py --verbose
```

### Phase Gate Checklist

Each phase gate runs:

1. **Linters**
   - Ruff: Code quality checks
   - Black: Code formatting
   - Mypy: Type checking

2. **Unit Tests**
   - All unit tests must pass
   - Test individual components

3. **Integration Tests**
   - All integration tests must pass
   - Test component interactions

4. **Coverage Analysis**
   - Minimum 70% coverage (default)
   - 80% for strict mode
   - HTML report generated in `htmlcov/`

5. **Phase-Specific Tests**
   - Phase 2: Smart Fetcher tests
   - Phase 3: Cost Tracking tests
   - Phase 4: Knowledge Graph tests

### Exit Codes

- `0`: All tests passed
- `1`: One or more tests failed
- `130`: Tests interrupted by user

## Writing Tests

### Unit Test Example

```python
"""Unit tests for MyModule."""

import pytest
from unittest.mock import MagicMock

from curator.module import MyClass


class TestMyClass:
    """Test suite for MyClass."""

    def test_method_success(self, sample_config):
        """Test successful method execution."""
        obj = MyClass(config=sample_config)
        result = obj.method()

        assert result is not None
        assert result.status == "success"

    def test_method_with_mock(self, mock_github_client):
        """Test method with mocked dependency."""
        obj = MyClass(client=mock_github_client)
        result = obj.method()

        mock_github_client.some_method.assert_called_once()
        assert result is not None
```

### Integration Test Example

```python
"""Integration tests for CurationPipeline."""

import pytest
from unittest.mock import patch

from curator.pipeline import CurationPipeline


class TestCurationPipeline:
    """Integration tests for end-to-end curation."""

    @patch("curator.github.api_client.Github")
    def test_full_curation_flow(self, mock_github, sample_config):
        """Test complete curation workflow."""
        # Setup mocks
        mock_github.return_value.search_repositories.return_value = []

        # Run pipeline
        pipeline = CurationPipeline(config=sample_config)
        results = pipeline.run(theme="test theme")

        # Verify
        assert results is not None
        assert mock_github.called
```

### Using Fixtures

Common fixtures are defined in [tests/conftest.py](../tests/conftest.py):

```python
def test_with_fixtures(sample_config, sample_structured_intent, mock_github_client):
    """Test using shared fixtures."""
    # Use fixtures in your test
    pass
```

Available fixtures:
- `temp_dir`: Temporary directory
- `sample_config`: Sample configuration file
- `sample_structured_intent`: Sample intent structure
- `sample_search_result`: Sample GitHub search result
- `mock_github_client`: Mocked GitHub API client
- `mock_llm_provider`: Mocked LLM provider
- `mock_repo_analyzer`: Mocked repository analyzer
- `mock_evaluator`: Mocked metacognitive evaluator
- `sample_readme_content`: Sample README text
- `sample_repo_metadata`: Sample repository metadata

### Best Practices

1. **Test Naming**: Use descriptive names that explain what is being tested
   ```python
   def test_stage1_metadata_check_high_stars()  # Good
   def test_stage1()  # Bad
   ```

2. **One Assertion Per Test**: Focus on testing one thing at a time
   ```python
   def test_result_has_correct_decision():
       result = stage1_check()
       assert result.decision == Decision.CONTINUE

   def test_result_has_high_confidence():
       result = stage1_check()
       assert result.confidence > 0.7
   ```

3. **Use Mocks Appropriately**: Mock external dependencies, not internal logic
   ```python
   @patch("curator.github.api_client.Github")  # Good - external API
   def test_with_mock(mock_github):
       pass
   ```

4. **Arrange-Act-Assert Pattern**:
   ```python
   def test_method():
       # Arrange
       obj = MyClass()

       # Act
       result = obj.method()

       # Assert
       assert result == expected
   ```

5. **Test Edge Cases**: Test boundary conditions, errors, and edge cases
   ```python
   def test_empty_input()
   def test_none_input()
   def test_invalid_input()
   def test_rate_limit_exceeded()
   ```

## CI/CD Integration

### GitHub Actions

The project uses GitHub Actions for continuous integration. Tests run automatically on:

- **Push** to `main`, `develop`, or `feature/*` branches
- **Pull requests** to `main` or `develop`
- **Manual trigger** with optional phase parameter

See [.github/workflows/test-phase-gate.yml](../.github/workflows/test-phase-gate.yml) for configuration.

### Workflow Jobs

1. **test**: Runs on Python 3.9, 3.10, 3.11, 3.12
   - Linters
   - Unit tests
   - Integration tests
   - Coverage analysis

2. **phase-gate-strict**: Runs on PRs
   - Strict mode with 80% coverage requirement
   - Verbose output

3. **security-scan**: Security checks
   - Bandit: Security vulnerability scan
   - Safety: Known vulnerability check

### Status Badges

Add to README.md:

```markdown
![Tests](https://github.com/IntentHub/github-curator/workflows/Phase%20Gate%20Tests/badge.svg)
[![codecov](https://codecov.io/gh/IntentHub/github-curator/branch/main/graph/badge.svg)](https://codecov.io/gh/IntentHub/github-curator)
```

## Coverage Requirements

### Minimum Coverage

- **Default**: 70% minimum coverage
- **Strict Mode**: 80% minimum coverage
- **Goal**: 90%+ coverage for critical paths

### Viewing Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=curator --cov-report=html

# Open in browser
open htmlcov/index.html
```

### Coverage by Module

Aim for higher coverage in critical modules:

- `curator/github/smart_fetcher.py`: 90%+
- `curator/core/metacognitive_eval.py`: 90%+
- `curator/core/intent_structuring.py`: 85%+
- `curator/github/api_client.py`: 80%+
- Other modules: 70%+

### Excluding Code from Coverage

```python
def debug_only_function():  # pragma: no cover
    """This function is not tested."""
    pass
```

## Troubleshooting

### Tests Failing Locally

1. Ensure dependencies are installed:
   ```bash
   pip install -e ".[dev]"
   ```

2. Check Python version:
   ```bash
   python --version  # Should be 3.9+
   ```

3. Clear cache and retry:
   ```bash
   pytest --cache-clear
   ```

### Import Errors

Ensure the package is installed in development mode:
```bash
pip install -e .
```

### Mock Issues

If mocks aren't working:
1. Check mock paths match actual import paths
2. Ensure `@patch` decorators are in correct order (bottom-up)
3. Use `mock_open` for file operations

### Slow Tests

Run specific tests instead of full suite:
```bash
pytest tests/unit/test_smart_fetcher.py -v
```

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [unittest.mock documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py documentation](https://coverage.readthedocs.io/)
- [Ruff documentation](https://docs.astral.sh/ruff/)
- [Mypy documentation](https://mypy.readthedocs.io/)

## Getting Help

If you have questions about testing:

1. Check this documentation
2. Look at existing tests for examples
3. Open an issue on GitHub
4. Consult the team on Slack/Discord
