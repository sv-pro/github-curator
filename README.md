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

```bash
# Clone the repository
git clone https://github.com/IntentHub/github-curator.git
cd github-curator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

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

# Generate detailed trace
python -m curator curate "well-documented APIs" --trace --output results/
```

## Project Status

This project is currently in the specification phase. The architecture and modules described above represent the planned implementation from [instructions.md](instructions.md).

## Documentation

- [CLAUDE.md](CLAUDE.md): Development guidance for Claude Code
- [instructions.md](instructions.md): Complete implementation specification

## License

MIT License - see [LICENSE](LICENSE) file for details

## Contributing

Contributions are welcome! Please ensure:
- Code follows the architectural principles outlined in the specification
- All evaluations include explicit confidence tracking
- Changes maintain traceability from intent to results
- Validation rules are respected

## Related Projects

This project is part of the IntentHub ecosystem, demonstrating principles of structured intent representation and metacognitive evaluation.
