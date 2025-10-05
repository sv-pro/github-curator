# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GitHub Curator is a tool for intelligent curation of GitHub repositories that demonstrates IntentHub principles. It structures natural language curation themes into dimensional evaluations, performs metacognitive repository assessment, and generates validated results with full traceability.

## Architecture

The system follows a structured pipeline: Intent Structuring → Metacognitive Evaluation → Validation → Reflection

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

### Data Flow

```
User Theme → Structured Intent → GitHub Search → Repository Analysis →
Metacognitive Evaluation → Validation → Results → Reflection → Reports
```

## Configuration

Main configuration in `config/curator.yaml`:
- Intent structuring parameters (dimension weights, constraints)
- GitHub API settings (search limits, rate limiting)
- Evaluation thresholds (confidence levels, minimum indicators)
- Validation rules (strict mode, warning thresholds)
- Output formats (markdown, JSON, HTML traces)

## Key Principles

- **Transparency**: Every evaluation traces to specific evidence
- **Metacognition**: Explicit confidence representation at all levels
- **Validation**: Consistency checks at intent, evaluation, and result levels
- **Reflection**: Pattern analysis for continuous improvement
- **Composability**: Dimensions combine predictably with clear interfaces

## Development Notes

This project is in specification phase - the `instructions.md` file contains the complete implementation specification. The architecture demonstrates IntentHub principles through structured evaluation, metacognitive assessment, and reflective learning.

No build or test commands are available yet as implementation has not begun. The project structure and modules described above represent the planned architecture from the specification.