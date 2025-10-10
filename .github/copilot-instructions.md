# GitHub Copilot Instructions

This file provides guidance to GitHub Copilot when working with code in this repository.

## Project Overview

GitHub Curator is a tool for intelligent curation of GitHub repositories that demonstrates IntentHub principles. It structures natural language curation themes into dimensional evaluations, performs metacognitive repository assessment, and generates validated results with full traceability.

## Architecture

The system follows a structured pipeline: Intent Structuring → Metacognitive Evaluation → Validation → Reflection

### Core Modules

- **curator/core/**: Core functionality (intent_structuring.py, metacognitive_eval.py, validation.py, reflection.py)
- **curator/github/**: GitHub integration (api_client.py, repo_analyzer.py, smart_fetcher.py)
- **curator/knowledge/**: Knowledge management (criteria_graph.py, evaluation_rules.py)
- **curator/outputs/**: Output generation (report_generator.py, trace_visualizer.py)

## Key Principles

- **Transparency**: Every evaluation traces to specific evidence
- **Metacognition**: Explicit confidence representation at all levels
- **Validation**: Consistency checks at intent, evaluation, and result levels
- **Reflection**: Pattern analysis for continuous improvement
- **Composability**: Dimensions combine predictably with clear interfaces

## Session Management & Context Preservation

### When I say "save context" or "update context"

Please analyze the current session and update `.claude/context.md` with:

1. **Recent changes and commits** since last update
2. **Current branch and uncommitted changes** (use `git status`, `git diff --stat`)
3. **What was implemented/fixed**:
   - Key files modified with paths
   - Technical decisions and their rationale
   - Any workarounds or temporary solutions
4. **Current task context**:
   - What we're working on
   - Goals and objectives
   - Current phase/milestone
5. **Next steps and pending tasks**
6. **Any blockers or important notes**

### When I say "load context" or "read context"

Please read `.claude/context.md` and provide a brief overview including:

1. **Recent commits and accomplishments**
2. **Current branch and status** (clean/uncommitted changes)
3. **Key technical details** (Smart Fetcher, tests, implementations)
4. **Next steps and immediate options**
5. **Any important notes or blockers**

Keep the summary concise and actionable. Highlight what's ready to work on next.

### Context Update Triggers

Update context at these times:
- Before committing significant features
- After completing a phase or major milestone
- When switching branches or starting new work
- At natural breakpoints (end of day, before reviews)
- When I explicitly request it

### Context Format

Keep the context:
- **Concise but comprehensive** - focus on last 1-2 sessions
- **Actionable** - include specific file paths and line numbers
- **Technical** - document decisions, not just what changed
- **Forward-looking** - clear next steps

## Testing and Quality

Before suggesting commits or completions:

- Mention running `make test-phase-gate` before committing to feature branches
- Mention running `make test-phase-gate-strict` before creating pull requests
- Ensure coverage doesn't drop below 70%
- All tests must pass before merging

Available test commands:
```bash
make test              # Run all tests with coverage
make test-unit         # Unit tests only
make test-integration  # Integration tests only
make test-coverage     # Detailed coverage report
make test-phase-gate   # Quality checkpoint tests
```

See [TESTING.md](docs/TESTING.md) for comprehensive testing guide.

## Code Style and Conventions

- Use **pytest** for testing (not unittest)
- Use **pytest-mock** for mocking (avoid manual mock setup)
- Use **type hints** throughout (mypy enforced)
- Follow **PEP 8** (black + ruff enforced via pre-commit)
- Write **docstrings** for public APIs
- Include **confidence scores** in evaluations
- Maintain **traceability** from intent to results

## Smart Repo Fetcher Context

When working on the Smart Repo Fetcher (`curator/github/smart_fetcher.py`):

- 4-stage progressive analysis pipeline
- Tests in `tests/unit/github/test_smart_fetcher.py`
- Configuration in `config/curator.yaml` under `smart_fetch` section
- Provides 50-70% cost reduction, 3-5x speedup

**Known limitations**:
- Stage 4 (code analysis) is stubbed
- LLM quick check in Stage 2 is stubbed (enable_quick_llm: false)
- No caching yet
- No parallel stage execution yet

## Documentation Structure

- **User docs**: `docs/USAGE.md`, `docs/LLM_PROVIDERS.md`, `QUICKSTART.md`
- **Developer docs**: `docs/TESTING.md`, `docs/TEST_QUICK_REFERENCE.md`, `CONTRIBUTING.md`, `docs/PROJECT_PLAN.md`
- **Reference**: `TESTING_SUITE_SUMMARY.md`, `IMPLEMENTATION_SUMMARY.md`

When updating documentation:
- Keep README.md high-level with links to detailed docs
- Update PROJECT_PLAN.md when completing phases
- Cross-reference related docs for discoverability

## Current Project Status

- ✅ **Phase 0**: Foundation and core architecture
- ✅ **Phase 1**: Declarative pipeline and multi-provider LLM support
- ✅ **Phase 2**: Smart Repo Fetcher (50-70% cost reduction, 3-5x speedup)
- ✅ **Phase 2.5**: Automated test suite (40+ tests, CI/CD, phase gates)
- 📋 **Phase 3**: Cost tracking + semantic search (planned)
- 📋 **Phase 4**: Criteria graph + validation rules (planned)
- 📋 **Phase 5**: Reflection + learning (planned)

## Git Workflow

- Feature work happens on feature branches (e.g., `feature/smart-repo-fetcher`)
- Main branch is used for PRs (check git status for actual main branch name)
- Use conventional commits when possible
- Include "🤖 Generated with [Claude Code](https://claude.com/claude-code)" or similar attribution in commits when appropriate

---

**Note**: For Claude Code-specific features (like `/save-context` slash command), see `CLAUDE.md`. This file provides compatible instructions for GitHub Copilot.
