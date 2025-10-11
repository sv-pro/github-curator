# Claude Code Context

Last updated: 2025-10-11
Branch: `feature/research-architecture`

## Session Summary

### What Was Accomplished This Session

**Milestone 1**: Repository Tracking System - Committed ✅

- Built complete git-based tracking (~1,100 lines)
- Commands: `track`, `list-tracked`, `curate-tracked`, `review`
- Git-native storage with LLM-generated reviews
- Tested successfully with real repository

**Milestone 2**: Research Architecture Redesign - Planned & Started 🚧

- Analyzed command confusion, designed new architecture
- Created comprehensive design document (40+ page plan)
- Started Phase 1 implementation: ResearchManager class
- New feature branch created

**Milestone 3**: Research Module Foundation - In Progress ⚙️

- Implemented `ResearchManager` class (~340 lines)
- Workspace CRUD operations (create, list, load, delete)
- YAML-based config persistence
- Ready for CLI command integration

## Recent Commits

```bash
c1c06d2 docs: Add research architecture redesign plan
9cf6253 feat: Add repository tracking system with git-native storage
f302163 docs: Update copilot-instructions with load-context command
a7cb2d0 feat: Add /load-context slash command for reading session context
002e53d feat: Add comprehensive test suite and CI/CD infrastructure (Phase 2.5)
```

## Current Status

### Branch Status

- **Branch**: `feature/research-architecture` (NEW)
- **Status**: Uncommitted changes
- **Untracked files**: `curator/research/` (2 files, ~340 lines)
- **Latest commit**: Research architecture redesign plan (c1c06d2)
- **Parent branch**: `feature/smart-repo-fetcher`

### What's Working

1. **Repository Tracking** ([curator/tracking/](curator/tracking/))
   - Git-native storage in `~/.github-curator/tracked/`
   - Commands: `track`, `list-tracked`, `curate-tracked`, `review`
   - Files: `.curator/CURATION.md` (history) + `.curator/REVIEW.md` (current)
   - LLM-generated rich reviews
   - Full git traceability with tags

2. **Smart Repo Fetcher** ([curator/github/smart_fetcher.py](curator/github/smart_fetcher.py))
   - Multi-stage analysis (50-70% cost reduction)
   - 40+ passing tests
   - Fully integrated

3. **Testing Infrastructure**
   - Phase gates: `make test-phase-gate`, `make test-phase-gate-strict`
   - 70%+ coverage
   - CI/CD pipeline

## Changes This Session (Uncommitted)

### New Module: Research Management (~340 lines)

**[curator/research/manager.py](curator/research/manager.py)** (335 lines):

- `ResearchManager` class - Workspace lifecycle management
  - `create()` - Initialize new research workspace
  - `exists()` - Check if research exists
  - `load_config()` / `save_config()` - YAML persistence
  - `list_research()` - List all research workspaces
  - `delete()` - Remove research workspace
  - Helper methods for paths (repos/, snapshots/, reports/)
- `ResearchConfig` dataclass - Configuration structure
  - Stores: name, query, created, theme, search params, snapshots
  - YAML serialization/deserialization
- `ResearchInfo` dataclass - Runtime information
  - Computed: repo_count, snapshot_count, last_updated
  - Used for listing and display

**[curator/research/\_\_init\_\_.py](curator/research/__init__.py)** (5 lines):

- Module exports: `ResearchManager`, `ResearchConfig`, `ResearchInfo`

**Workspace Structure** (created by ResearchManager):

```text
~/.github-curator/research/<topic>/
├── config.yaml              # Research configuration (YAML)
├── repos/                   # Cloned repositories
│   └── org/repo/           # Will contain .curator/ files
├── snapshots/              # Point-in-time evaluations (JSON)
└── reports/                # Generated content (Markdown)
```

**Key Design Decisions**:

1. **Name sanitization**: Research names converted to filesystem-safe format
   - Lowercase, hyphens for spaces, alphanumeric only
   - Example: "Python Async 2025" → "python-async-2025"

2. **YAML config**: Human-readable, git-friendly
   - Stores theme (focus/exclude) and search parameters
   - Tracks snapshot metadata for quick lookups

3. **Lazy loading**: Repo/snapshot counts computed on demand
   - Avoids expensive filesystem scans during list operations

4. **Reusable paths**: Separate methods for repos/, snapshots/, reports/
   - Makes it easy for other components to find workspace resources

## Next Steps: Research Architecture Redesign

### Implementation Progress

**Phase 1: Core Infrastructure** (Days 1-2) - IN PROGRESS

- ✅ Create `curator/research/` module
- ✅ `ResearchManager` class with workspace CRUD
- ✅ `ResearchConfig` with YAML persistence
- ✅ Workspace directory structure
- ⏳ CLI commands (next up):
  - `curator research init` - Create workspace
  - `curator research list` - Show all research
  - `curator research show` - Display research details
  - `curator research add` - Add repos to research

**Next**: Integrate ResearchManager into CLI

### User's Workflow (Design Goal)

**Time-series research**: Track topic evolution over time

1. Research setup → Collect repos → Baseline evaluation
2. Publish initial report/post
3. Periodic updates:
   - Topic refresh: Discover new repos
   - Repo updates: Track changes in existing repos
4. Re-publish with evolution comparison

### Proposed Solution

**Research Workspaces** - Self-contained topic research:

```text
~/.github-curator/research/<topic>/
├── config.yaml              # Research config
├── repos/                   # Cloned repos with .curator/ files
├── snapshots/               # Point-in-time evaluations (JSON)
└── reports/                 # Generated content
```

**New Command Structure**:

```bash
# Setup
curator research init "python-async-2025" --query "..."
curator research collect python-async-2025 --limit 50
curator research add python-async-2025 <repo-url>

# Evaluation
curator research snapshot python-async-2025 --name "baseline"
curator research diff python-async-2025 --from baseline --to update

# Updates
curator research refresh python-async-2025 --sync      # Pull code
curator research refresh python-async-2025 --discover  # Find new repos
curator research refresh python-async-2025 --all       # Both

# Publishing
curator research report python-async-2025 --snapshot baseline
curator research report python-async-2025 --compare-from baseline --compare-to update
```

**Command Mapping**:

- `curate` → `research collect`
- `track` → `research add`
- `curate-tracked` → `research snapshot`
- `review` → `research refresh --sync`
- `collect` → Removed (merged into `research collect`)
- `mark` → Deferred

### Full Implementation Plan

See [docs/RESEARCH_ARCHITECTURE_REDESIGN.md](docs/RESEARCH_ARCHITECTURE_REDESIGN.md) for complete 5-phase plan.

**Current Phase**: Phase 1 (Core Infrastructure) - 60% complete

**Immediate Next Tasks**:

1. Add CLI commands to [curator/\_\_main\_\_.py](curator/__main__.py):
   - `curator research init` - Create new research workspace
   - `curator research list` - Show all research workspaces
   - `curator research show <name>` - Display research details
   - `curator research add <name> <repo-url>` - Add repos to research
2. Test commands with real usage
3. Commit Phase 1 implementation
4. Move to Phase 2 (Evaluation & Snapshots)

## Key Technical Context

### Components Available for Reuse

1. **Repository Tracking** ([curator/tracking/](curator/tracking/)) - Committed
   - `RepoTracker`: Git operations (clone, pull, branch management)
   - `CurationFileManager`: CURATION.md formatting
   - `ReviewGenerator`: LLM-generated reviews
   - Will be used by research system for repo management

2. **Evaluation Pipeline** - Existing
   - `IntentStructurer`: Theme → evaluation dimensions
   - `MetacognitiveEvaluator`: Repository evaluation with confidence
   - `GitHubAPIClient`: GitHub API with rate limiting
   - `RepositoryAnalyzer`: Content analysis
   - Will be used by `research snapshot` and `research collect`

3. **Smart Repo Fetcher** ([curator/github/smart_fetcher.py](curator/github/smart_fetcher.py))
   - Multi-stage analysis for cost optimization
   - Will be used by `research collect` for discovery

## Important Notes for Next Session

### What to Do Next

1. **Continue Phase 1**: Add CLI commands
   - Integrate `ResearchManager` into `curator/__main__.py`
   - Implement `research` command group with subcommands
   - Test workspace creation and management

2. **When Phase 1 is complete**:
   - Commit with: "feat: Add research workspace management (Phase 1)"
   - Test suite for ResearchManager
   - Move to Phase 2: Evaluation & Snapshots

### Design Decisions Made

- Research names are sanitized for filesystem safety
- YAML config for human-readability and git-friendliness
- Workspace structure: config.yaml + repos/ + snapshots/ + reports/
- Reuse existing tracking/evaluation components
- Self-contained workspaces (no shared state between research topics)

### Key Files

- Design: [docs/RESEARCH_ARCHITECTURE_REDESIGN.md](docs/RESEARCH_ARCHITECTURE_REDESIGN.md)
- Implementation: [curator/research/manager.py](curator/research/manager.py)
- CLI integration: [curator/\_\_main\_\_.py](curator/__main__.py) (next up)

## Session Wrap-Up

### Completed Today

1. ✅ **Tracking System** - Fully implemented and tested
2. ✅ **Architecture Redesign** - Complete design document created
3. ✅ **Research Module** - Core workspace management implemented
4. ✅ **New Branch** - `feature/research-architecture` created

### In Progress

- **Phase 1 CLI Integration** - Need to add commands to `__main__.py`

### Key Insights

- User workflow is time-series research (not one-off curation)
- Commands need clear separation: setup → collect → snapshot → publish → refresh
- Research workspaces are self-contained (no conflicts between topics)
- Snapshot comparison is core value (track evolution over time)
- Reuse existing evaluation/tracking infrastructure
