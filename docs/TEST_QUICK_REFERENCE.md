# Test Quick Reference

Quick reference for common testing commands and workflows.

## Common Commands

```bash
# Run all tests
make test

# Run specific test types
make test-unit                  # Unit tests only
make test-integration          # Integration tests only
make test-coverage             # With HTML coverage report

# Phase gate testing
make test-phase-gate           # All tests with phase gate checks
make test-phase-gate PHASE=2   # Phase 2 specific tests
make test-phase-gate-strict    # Strict mode (80% coverage)

# Code quality
make lint                      # Run linters
make format                    # Format code
make check                     # Lint + test
```

## pytest Commands

```bash
# Basic
pytest                              # Run all tests
pytest -v                          # Verbose output
pytest -s                          # Show print statements
pytest -x                          # Stop on first failure
pytest --lf                        # Run last failed tests

# Specific tests
pytest tests/unit/                 # Unit tests only
pytest tests/integration/          # Integration tests only
pytest tests/unit/test_smart_fetcher.py  # Specific file
pytest -k "metadata"               # Tests matching pattern

# Coverage
pytest --cov=curator               # Show coverage
pytest --cov=curator --cov-report=html  # HTML report
pytest --cov-fail-under=70         # Fail if <70% coverage

# Debugging
pytest --pdb                       # Drop to debugger on failure
pytest --tb=short                  # Short traceback
pytest --tb=no                     # No traceback
```

## Phase Gate Quick Check

Before committing or creating PR:

```bash
# Quick check (2-3 minutes)
make lint && make test-unit

# Full check (5-10 minutes)
make test-phase-gate

# Comprehensive (10-15 minutes)
make test-phase-gate-strict
```

## Writing Tests Cheat Sheet

### Basic Test Structure

```python
def test_feature_name():
    """Test description."""
    # Arrange
    setup_data = create_test_data()

    # Act
    result = function_under_test(setup_data)

    # Assert
    assert result == expected_value
```

### Using Fixtures

```python
def test_with_fixtures(sample_config, mock_github_client):
    """Test using fixtures from conftest.py."""
    obj = MyClass(config=sample_config, client=mock_github_client)
    result = obj.method()
    assert result is not None
```

### Mocking

```python
from unittest.mock import MagicMock, patch

# Mock object
@patch("curator.module.ExternalClass")
def test_with_mock(mock_class):
    mock_class.return_value.method.return_value = "mocked"
    result = function_that_uses_external_class()
    assert result == "mocked"

# Mock return value
mock_obj = MagicMock()
mock_obj.method.return_value = "value"
mock_obj.method.side_effect = Exception("error")
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_multiply_by_two(input, expected):
    """Test multiple inputs."""
    assert multiply_by_two(input) == expected
```

## Fixtures Reference

From `tests/conftest.py`:

| Fixture | Description |
|---------|-------------|
| `temp_dir` | Temporary directory |
| `sample_config` | Sample config file |
| `sample_structured_intent` | Sample intent |
| `sample_search_result` | Sample GitHub repo |
| `mock_github_client` | Mocked GitHub client |
| `mock_llm_provider` | Mocked LLM |
| `mock_repo_analyzer` | Mocked analyzer |
| `mock_evaluator` | Mocked evaluator |
| `sample_readme_content` | Sample README |
| `sample_repo_metadata` | Sample metadata |

## Coverage Targets

| Module | Target | Status |
|--------|--------|--------|
| smart_fetcher.py | 90% | 🎯 Critical |
| metacognitive_eval.py | 90% | 🎯 Critical |
| intent_structuring.py | 85% | ⚡ High |
| api_client.py | 80% | ⚡ High |
| Other modules | 70% | ✓ Standard |

## CI/CD Status Checks

Pull requests must pass:

- ✓ Linters (ruff, black, mypy)
- ✓ Unit tests (all Python versions)
- ✓ Integration tests
- ✓ Coverage ≥70%
- ✓ Security scan (bandit, safety)
- ✓ Strict phase gate (for main/develop)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Import errors | `pip install -e ".[dev]"` |
| Old cache | `pytest --cache-clear` |
| Slow tests | Run specific: `pytest tests/unit/test_file.py` |
| Mock not working | Check patch path matches import |
| Coverage too low | Run `pytest --cov-report=html` and check `htmlcov/` |

## Git Workflow

```bash
# Before committing
make lint                  # Fix any issues
make test-unit            # Run unit tests

# Before pushing
make test-phase-gate      # Full check

# Before creating PR
make test-phase-gate-strict  # Strict validation
```

## Environment Variables

```bash
# Required for real API calls
export ANTHROPIC_API_KEY="your-key"
export GITHUB_TOKEN="your-token"

# For tests (mocked by default)
# No need to set - conftest.py mocks them
```

## Performance

Typical run times:

| Command | Time | Use Case |
|---------|------|----------|
| `make lint` | 10-20s | Quick check |
| `make test-unit` | 1-2 min | Unit tests only |
| `make test-integration` | 2-3 min | Integration tests |
| `make test-coverage` | 3-5 min | Full with coverage |
| `make test-phase-gate` | 5-10 min | Complete validation |
| `make test-phase-gate-strict` | 10-15 min | Comprehensive |

## Quick Decision Tree

```
Need to commit?
├─ Yes → make lint && make test-unit
└─ No → Skip

Need to push?
├─ Yes → make test-phase-gate
└─ No → Skip

Need to create PR?
├─ Yes → make test-phase-gate-strict
└─ No → Skip
```
