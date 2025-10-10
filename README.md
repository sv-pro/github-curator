# GitHub Curator

Intelligent curation of GitHub repositories demonstrating IntentHub principles.

## Overview

GitHub Curator is a tool that transforms natural language curation themes into structured, validated repository assessments. It demonstrates IntentHub principles through:

- **Intent Structuring**: Transforms natural language themes into dimensional evaluations
- **Metacognitive Evaluation**: Assesses repositories with explicit confidence tracking
- **Validation**: Ensures consistency across intent, evaluation, and results
- **Reflection**: Analyzes patterns and suggests improvements

## Architecture

The system follows a structured pipeline:

```
User Theme → Structured Intent → GitHub Search → Repository Analysis →
Metacognitive Evaluation → Validation → Results → Reflection → Reports
```

### Core Modules

- **curator/core/**: Core functionality
  - `intent_structuring.py`: Transforms natural language themes into structured evaluation dimensions
  - `metacognitive_eval.py`: Evaluates repositories with explicit confidence tracking
  - `validation.py`: Validates intent structure, evaluations, and result consistency
  - `reflection.py`: Analyzes patterns and suggests improvements

- **curator/github/**: GitHub integration
  - `api_client.py`: GitHub API client with rate limiting
  - `repo_analyzer.py`: Repository content analysis
  - `smart_fetcher.py`: Multi-stage adaptive repository analysis (50-70% cost reduction)

- **curator/knowledge/**: Knowledge management
  - `criteria_graph.py`: Evaluation criteria definitions
  - `evaluation_rules.py`: Validation rule engine

- **curator/outputs/**: Output generation
  - `report_generator.py`: Markdown and JSON report generation
  - `trace_visualizer.py`: Interactive trace viewer (HTML)

## Key Principles

- **Transparency**: Every evaluation traces to specific evidence
- **Metacognition**: Explicit confidence representation at all levels
- **Validation**: Consistency checks at intent, evaluation, and result levels
- **Reflection**: Pattern analysis for continuous improvement
- **Composability**: Dimensions combine predictably with clear interfaces

## Installation

### Quick Install

```bash
# Clone the repository
git clone https://github.com/IntentHub/github-curator.git
cd github-curator

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with pip (uses modern pyproject.toml)
pip install -e .

# For development (includes testing, linting, type checking)
pip install -e ".[dev]"

# Optional: Install additional LLM providers
pip install -e ".[openai]"        # OpenAI support
pip install -e ".[google]"        # Google Gemini support
pip install -e ".[ollama]"        # Ollama (local) support
pip install -e ".[all-providers]" # All providers

# Or use Make
make install      # production
make install-dev  # development
```

### Prerequisites

- Python 3.9 or higher
- **LLM API Key** (choose one):
  - Anthropic Claude API key ([get one here](https://console.anthropic.com/)) - **Default**
  - OpenAI API key ([get one here](https://platform.openai.com/api-keys))
  - Google API key ([get one here](https://makersuite.google.com/app/apikey))
  - Ollama ([install locally](https://ollama.com)) - Free, no API key needed
- GitHub Personal Access Token ([create one here](https://github.com/settings/tokens))

### Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
# Default: Anthropic Claude
ANTHROPIC_API_KEY=your_key_here
GITHUB_TOKEN=your_token_here

# OR use a different LLM provider:
# CURATOR_LLM_PROVIDER=openai
# OPENAI_API_KEY=your_key_here

# OR use Google Gemini:
# CURATOR_LLM_PROVIDER=google
# GOOGLE_API_KEY=your_key_here

# OR use Ollama (local, free):
# CURATOR_LLM_PROVIDER=ollama
# (No API key needed, just install and run Ollama)

# Verify setup
python -m curator setup
# Or: make setup
```

See [LLM Provider Guide](docs/LLM_PROVIDERS.md) for detailed configuration options.

## Configuration

Main configuration in [config/curator.yaml](config/curator.yaml):
- Intent structuring parameters (dimension weights, constraints)
- GitHub API settings (search limits, rate limiting)
- Evaluation thresholds (confidence levels, minimum indicators)
- Validation rules (strict mode, warning thresholds)
- Output formats (markdown, JSON, HTML traces)

## Usage

```bash
# Basic usage
python -m curator curate "repositories for machine learning visualization"

# With custom configuration
python -m curator curate "educational Python projects" --config config/custom.yaml

# Smart fetching modes (adaptive analysis for cost reduction)
python -m curator curate "well-documented APIs" --fetch-mode fast      # Quick filtering
python -m curator curate "production-ready tools" --fetch-mode standard  # Balanced (default)
python -m curator curate "comprehensive review" --fetch-mode thorough   # Deep analysis

# Disable smart fetching (analyze all repositories fully)
python -m curator curate "theme" --disable-smart-fetch

# Generate detailed trace
python -m curator curate "well-documented APIs" --trace --output results/
```

See [USAGE.md](docs/USAGE.md) for complete usage guide.

## Project Status

✨ **Implementation Complete!** The GitHub Curator is now fully functional with all core features implemented.

- ✅ Intent structuring with Claude
- ✅ GitHub API integration
- ✅ Metacognitive evaluation
- ✅ Multi-level validation
- ✅ Reflection and pattern analysis
- ✅ Multi-format reporting (Markdown, JSON, HTML)
- ✅ CLI interface
- ✅ Smart Repo Fetcher (50-70% cost reduction, 3-5x speedup)
- ✅ Multi-provider LLM support (Anthropic, OpenAI, Google, Ollama)
- ✅ Comprehensive automated test suite

See [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for details.

## Documentation

### User Documentation
- [USAGE.md](docs/USAGE.md): Comprehensive usage guide
- [LLM_PROVIDERS.md](docs/LLM_PROVIDERS.md): Multi-provider LLM configuration
- [QUICKSTART.md](QUICKSTART.md): Quick start guide

### Developer Documentation
- [TESTING.md](docs/TESTING.md): Testing strategy and practices
- [TEST_QUICK_REFERENCE.md](docs/TEST_QUICK_REFERENCE.md): Testing cheat sheet
- [CONTRIBUTING.md](CONTRIBUTING.md): Development guidelines
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md): Implementation details
- [PROJECT_PLAN.md](docs/PROJECT_PLAN.md): Project roadmap and phases
- [CLAUDE.md](CLAUDE.md): Claude Code integration

### Reference
- [instructions.md](instructions.md): Original specification
- [TESTING_SUITE_SUMMARY.md](TESTING_SUITE_SUMMARY.md): Test suite overview

## License

MIT License - see [LICENSE](LICENSE) file for details

## Testing

The project includes a comprehensive automated test suite:

```bash
# Run all tests
make test

# Run unit tests only
make test-unit

# Run integration tests only
make test-integration

# Run with coverage report
make test-coverage

# Run phase gate tests (quality checkpoint)
make test-phase-gate

# Run strict phase gate (for PRs)
make test-phase-gate-strict
```

See [TESTING.md](docs/TESTING.md) for comprehensive testing guide and [TEST_QUICK_REFERENCE.md](docs/TEST_QUICK_REFERENCE.md) for quick reference.

## Contributing

Contributions are welcome! Please ensure:
- Code follows the architectural principles outlined in the specification
- All evaluations include explicit confidence tracking
- Changes maintain traceability from intent to results
- Validation rules are respected
- **Tests pass**: Run `make test-phase-gate` before submitting PRs
- **Code quality**: Run `make lint` to check code style

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## Related Projects

This project is part of the IntentHub ecosystem, demonstrating principles of structured intent representation and metacognitive evaluation.
