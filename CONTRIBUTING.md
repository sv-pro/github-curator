# Contributing to GitHub Curator

Thank you for your interest in contributing to GitHub Curator! This document provides guidelines and instructions for contributing.

## Development Setup

1. **Fork and clone the repository:**

```bash
git clone https://github.com/your-username/github-curator.git
cd github-curator
```

2. **Create a virtual environment:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install in development mode with all tools:**

```bash
# Modern approach with pyproject.toml
pip install -e ".[dev]"

# Or use Make
make install-dev
```

4. **Set up pre-commit hooks (optional but recommended):**

```bash
pip install pre-commit
pre-commit install
```

5. **Set up environment variables:**

```bash
cp .env.example .env
# Edit .env with your API keys
```

6. **Verify setup:**

```bash
python -m curator setup
# Or: make setup
```

## Architecture Overview

GitHub Curator follows a pipeline architecture demonstrating IntentHub principles:

```
Intent Structuring → GitHub Search → Context Analysis →
Metacognitive Evaluation → Validation → Reflection → Reports
```

### Key Modules

- **[curator/core/intent_structuring.py](curator/core/intent_structuring.py)**: Transforms natural language themes into structured dimensions
- **[curator/github/api_client.py](curator/github/api_client.py)**: GitHub API integration with rate limiting
- **[curator/github/repo_analyzer.py](curator/github/repo_analyzer.py)**: Repository context gathering
- **[curator/core/metacognitive_eval.py](curator/core/metacognitive_eval.py)**: Evaluation with explicit confidence tracking
- **[curator/core/validation.py](curator/core/validation.py)**: Multi-level consistency validation
- **[curator/core/reflection.py](curator/core/reflection.py)**: Pattern analysis and improvement suggestions
- **[curator/outputs/report_generator.py](curator/outputs/report_generator.py)**: Multi-format report generation

## Development Principles

### 1. Transparency
- Every evaluation must trace to specific evidence
- No scores without justification
- Clear attribution of confidence levels

### 2. Metacognition
- Explicit representation of certainty/uncertainty
- Identification of limitations and gaps
- Understanding of evaluation quality

### 3. Validation
- Validate at intent, evaluation, and result levels
- Check consistency and completeness
- Clear error messages

### 4. Reflection
- Analyze patterns in evaluations
- Suggest improvements
- Learn from experience

## Code Style

We use:
- **Black** for code formatting
- **Ruff** for linting
- **MyPy** for type checking

```bash
# Format code
black curator/ tests/

# Lint
ruff check curator/ tests/

# Type check
mypy curator/
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=curator --cov-report=html

# Run specific test
pytest tests/test_intent_structuring.py -v
```

### Writing Tests

- Place tests in `tests/` directory
- Name test files `test_*.py`
- Name test functions `test_*`
- Use descriptive test names
- Include docstrings explaining what is tested

Example:
```python
def test_intent_validation_checks_weights():
    """Test that intent validation verifies dimension weights sum to 1.0."""
    # Test implementation
```

## Making Changes

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Follow the architecture principles
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass

### 3. Commit Your Changes

Follow conventional commit format:

```bash
git commit -m "feat: add new evaluation dimension"
git commit -m "fix: correct confidence calculation"
git commit -m "docs: update usage examples"
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `chore`

### 4. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Pull Request Guidelines

- **Title**: Clear, descriptive title
- **Description**: Explain what and why
- **Tests**: Include tests for new features
- **Documentation**: Update relevant docs
- **Code Quality**: Passes all linters and tests

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] Commits follow conventional format
- [ ] No breaking changes (or clearly documented)
- [ ] Self-review completed

## Adding New Features

### Adding a New Dimension Type

1. Update `curator/knowledge/criteria_graph.py` with dimension definition
2. Add indicators to dimension specification
3. Update evaluation logic in `metacognitive_eval.py`
4. Add validation rules in `validation.py`
5. Write tests

### Adding a New Report Format

1. Add format handler to `report_generator.py`
2. Update configuration schema
3. Add format to CLI options
4. Document in USAGE.md
5. Add example output

### Adding a New Analysis Pattern

1. Add pattern detection logic to `reflection.py`
2. Define pattern structure in dataclasses
3. Add recommendation generation
4. Update report templates
5. Add tests for pattern detection

## Common Development Tasks

### Running the CLI in Development

```bash
# Run directly
python -m curator curate "your theme"

# Or use the installed command
curator curate "your theme"
```

### Debugging

```python
# Add to any module for debugging
import pdb; pdb.set_trace()

# Or use logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Testing with Mock Data

```python
from unittest.mock import Mock, patch

@patch('curator.github.api_client.Github')
def test_with_mock_github(mock_github):
    # Test implementation
    pass
```

## Documentation

- **README.md**: Project overview and quick start
- **docs/USAGE.md**: Comprehensive usage guide
- **instructions.md**: Implementation specification
- **CLAUDE.md**: Development guidance for Claude Code
- **Docstrings**: All public functions and classes

### Documentation Standards

- Use Google-style docstrings
- Include type hints
- Provide examples in docstrings
- Keep docs up to date with code changes

Example:
```python
def evaluate_repository(
    self,
    context: RepositoryContext,
    intent: StructuredIntent
) -> EvaluationReport:
    """Evaluate a repository against structured intent.

    Args:
        context: Repository context with gathered information
        intent: Structured intent with evaluation dimensions

    Returns:
        EvaluationReport with scores, evidence, and metacognitive notes

    Example:
        >>> evaluator = MetacognitiveEvaluator()
        >>> report = evaluator.evaluate_repository(context, intent)
        >>> print(report.overall_relevance)
        0.85
    """
```

## Getting Help

- **Issues**: Check [existing issues](https://github.com/IntentHub/github-curator/issues)
- **Discussions**: Use [GitHub Discussions](https://github.com/IntentHub/github-curator/discussions)
- **Documentation**: Read [docs/USAGE.md](docs/USAGE.md)
- **Specification**: Review [instructions.md](instructions.md)

## Code Review Process

1. Automated checks run on all PRs
2. At least one maintainer review required
3. All conversations must be resolved
4. CI must pass
5. Branch must be up to date with main

## Release Process

1. Update version in `setup.py` and `curator/__init__.py`
2. Update CHANGELOG.md
3. Create release branch
4. Tag release
5. Publish to PyPI

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

Feel free to open an issue or start a discussion. We're here to help!

---

Thank you for contributing to GitHub Curator! 🎉
