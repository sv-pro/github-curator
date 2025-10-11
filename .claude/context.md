# Claude Code Context

Last updated: 2025-10-11
Branch: `feature/smart-repo-fetcher`

## Session Summary

### What Was Accomplished This Session

**Major Milestone 1**: Repository Tracking System - Committed ✅

- Built complete git-based tracking (~1,100 lines)
- Committed to feature branch (9cf6253)
- Tested with real repository (anthropics/anthropic-sdk-python)

**Major Milestone 2**: Research Architecture Redesign - Planned 📋

- Analyzed command structure confusion
- Designed new architecture around time-series research workflow
- Created comprehensive design document

## Recent Commits

```bash
9cf6253 feat: Add repository tracking system with git-native storage
f302163 docs: Update copilot-instructions with load-context command
a7cb2d0 feat: Add /load-context slash command for reading session context
```

## Current Status

### Branch Status

- **Branch**: `feature/smart-repo-fetcher`
- **Status**: Clean working directory
- **Latest commit**: Repository tracking system (9cf6253)

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

## Next Steps: Research Architecture Redesign

### Problem Identified

Current commands are confusing:

- `curate` - One-off search + evaluation (not tracked)
- `curate-tracked` - Evaluate tracked repo (append to history)
- `review` - Update tracked repo (REVIEW.md only)
- Unclear when to use which

### User's Actual Workflow

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

### Implementation Plan

**Phase 1**: Core infrastructure (Days 1-2)

- [ ] Create `curator/research/` module
- [ ] `research init`, `list`, `add`, `show`
- [ ] Research workspace management
- [ ] Config.yaml structure

**Phase 2**: Evaluation & snapshots (Days 3-5)

- [ ] `research collect` - Search + evaluate + add
- [ ] `research snapshot` - Point-in-time evaluation
- [ ] `research refresh --sync` - Update all repos
- [ ] Snapshot JSON format

**Phase 3**: Discovery & comparison (Days 6-8)

- [ ] `research refresh --discover` - Find new repos
- [ ] `research diff` - Compare snapshots
- [ ] Change detection algorithms

**Phase 4**: Content generation (Days 9-11)

- [ ] `research report` - LLM-powered reports
- [ ] Initial + comparison report generation
- [ ] Markdown output

**Phase 5**: Migration & polish (Days 12-13)

- [ ] Deprecation warnings
- [ ] Migration guide
- [ ] Documentation updates

## Key Technical Details

### Repository Tracking System (Just Committed)

**Location**: [curator/tracking/](curator/tracking/)

**Modules**:

- `repo_tracker.py` (444 lines) - Git operations, cloning, syncing
- `curation_file_manager.py` (84 lines) - CURATION.md formatting
- `review_generator.py` (259 lines) - LLM-generated reviews
- `__init__.py` (7 lines) - Module exports

**Storage**: `~/.github-curator/tracked/{org}/{repo}/`

**Key Features**:

- Git-native (uses git for versioning)
- `.curator/` directory for files
- Dual files: CURATION.md (history) + REVIEW.md (current)
- Tag strategy: `curation-NNN-{date}` and `review-NNN-{date}`
- Branch syncing (`review` pulls all branches)

### Smart Repo Fetcher

**Location**: [curator/github/smart_fetcher.py](curator/github/smart_fetcher.py) (540+ lines)

**Modes**: fast → standard → thorough → exhaustive

**Performance**: 50-70% cost reduction, 3-5x speedup

**Tests**: [tests/unit/test_smart_fetcher.py](tests/unit/test_smart_fetcher.py) (13 tests)

## Documentation

### Existing

- [docs/REPO_TRACKING.md](docs/REPO_TRACKING.md) - Tracking system guide
- [docs/REVIEW_COMMAND.md](docs/REVIEW_COMMAND.md) - Review command reference
- [docs/TESTING.md](docs/TESTING.md) - Testing guide
- [examples/tracking_example.py](examples/tracking_example.py) - Demo script

### New

- [docs/RESEARCH_ARCHITECTURE_REDESIGN.md](docs/RESEARCH_ARCHITECTURE_REDESIGN.md) - Complete redesign plan

## Immediate Next Steps

1. **Review design doc** with user
2. **Create feature branch**: `feature/research-architecture`
3. **Start Phase 1 implementation**:
   - Create `curator/research/` module
   - Implement `ResearchManager` class
   - `research init` command
   - Research workspace structure

## Important Notes

### Design Decisions

**Research-scoped tracking**:

- Each topic is self-contained workspace
- Repos live under `research/<topic>/repos/`
- Multiple research projects don't conflict

**Snapshot-based evaluation**:

- Named snapshots (user-provided + timestamp)
- JSON format for comparison
- Enables time-series analysis

**Reuse existing components**:

- `IntentStructurer` for theme → dimensions
- `MetacognitiveEvaluator` for evaluation
- `RepoTracker` for git operations
- `ReviewGenerator` for LLM content

**New components needed**:

- `ResearchManager` - Workspace CRUD
- `SnapshotManager` - Snapshot creation/storage
- `ComparisonEngine` - Diff between snapshots
- `ReportGenerator` - Publishing-ready content

### Migration Strategy

- Keep old commands with deprecation warnings
- Provide migration script: old tracked → research
- Phase 5 handles smooth transition

## Session Notes

### User's Feedback

User clarified actual workflow is **time-series research**:

- Research topic evolution over time
- Periodic discovery + updates
- Publishing initial + update reports
- Need for meaningful comparison over time

This led to complete architecture redesign around "research workspaces" concept.

### Key Insights

1. **Separation needed**: Exploration vs tracking vs publishing
2. **Time-series is key**: Not just current state, but evolution
3. **Publishing focus**: Output should be blog-post ready
4. **Topic-scoped**: All repos belong to research topic
5. **Snapshot comparison**: Core value proposition

### What's Clear

- User workflow is well-defined now
- Research workspace concept maps perfectly
- Reuse existing tracking infrastructure
- Clean command structure
- Implementation plan is solid

### Ready to Implement

All design decisions made:

- ✅ Architecture designed
- ✅ Commands defined
- ✅ Data structures specified
- ✅ Implementation phases planned
- ✅ Migration strategy clear

**Waiting for**: User approval to start implementation
