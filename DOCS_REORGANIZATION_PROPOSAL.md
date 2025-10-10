# Documentation Reorganization Proposal

**Date**: 2025-10-09
**Status**: Proposal
**Goal**: Consolidate scattered documentation into a clear, navigable structure

---

## 🔍 Current State Analysis

### Current File Layout

```
Root directory:
├── README.md                      # Main entry point
├── QUICKSTART.md                  # Quick start guide
├── CONTRIBUTING.md                # Contribution guide
├── CLAUDE.md                      # Claude Code integration notes
├── instructions.md                # Original comprehensive specification
├── IMPLEMENTATION_SUMMARY.md      # Implementation status snapshot
├── PROJECT_SUMMARY.md             # Project overview + stats
├── MODERNIZATION.md               # Modern packaging migration notes
└── TODO.md                        # Gap analysis (NEW)

docs/:
├── PROJECT_PLAN.md                # Roadmap, phases, decisions
├── USAGE.md                       # Comprehensive usage guide
├── PHASE1_COMPLETE.md             # Phase 1 completion summary
├── PHASE1_LLM_PROVIDERS.md        # LLM provider implementation notes
├── LLM_PROVIDERS.md               # LLM provider user guide
├── DECLARATIVE_PIPELINE_DESIGN.md # Pipeline architecture notes
└── features/                      # Feature-specific design docs
    ├── mark-command.md
    ├── collect-command.md
    ├── cost-tracking.md
    ├── hybrid-storage.md
    ├── llm-abstraction.md
    └── declarative-pipeline.md
```

### Problems Identified

1. **Duplication**:
   - `LLM_PROVIDERS.md` vs `PHASE1_LLM_PROVIDERS.md` (user guide vs implementation notes)
   - `PROJECT_SUMMARY.md` vs `IMPLEMENTATION_SUMMARY.md` vs `PHASE1_COMPLETE.md` (overlapping status)
   - Multiple entry points with unclear purpose

2. **Organization**:
   - Unclear separation between user docs, developer docs, and project management
   - Status/history documents mixed with current documentation
   - Root directory cluttered with 9 markdown files

3. **Discoverability**:
   - New users: Which file to read first?
   - Contributors: Where is the architecture?
   - Project managers: Where is the roadmap?

4. **Maintenance**:
   - No clear ownership of "source of truth"
   - Outdated information scattered across files
   - Hard to keep synchronized

---

## 🎯 Proposed Structure

### Principles

1. **Audience-first**: Organize by who needs the information
2. **Single source of truth**: No duplicate content
3. **Progressive disclosure**: Simple → detailed
4. **Clear entry points**: Each audience knows where to start
5. **Easy maintenance**: Clear ownership and update paths

### New Organization

```
Root directory (Entry Points Only):
├── README.md                       # Main entry - "What is this?"
├── QUICKSTART.md                   # 5-minute start guide
├── CONTRIBUTING.md                 # How to contribute
├── CHANGELOG.md                    # Version history (NEW)
└── LICENSE                         # MIT license

docs/
├── index.md                        # Documentation hub (NEW)
│
├── user-guide/                     # For end users (NEW)
│   ├── installation.md             # Installation instructions
│   ├── configuration.md            # Config file reference
│   ├── usage.md                    # Basic → advanced usage
│   ├── commands.md                 # CLI command reference
│   ├── llm-providers.md            # LLM provider setup
│   ├── troubleshooting.md          # Common issues & solutions (NEW)
│   └── examples.md                 # Real-world examples (NEW)
│
├── developer-guide/                # For contributors (NEW)
│   ├── architecture.md             # System architecture
│   ├── development-setup.md        # Dev environment setup
│   ├── testing.md                  # Testing guide
│   ├── code-style.md               # Coding standards
│   ├── api-reference.md            # Python API docs (NEW)
│   └── contributing-guide.md       # Detailed contribution workflow
│
├── design/                         # Architecture & design decisions
│   ├── overview.md                 # High-level design (from instructions.md)
│   ├── intenthub-principles.md     # IntentHub demonstration (NEW)
│   ├── pipeline-architecture.md    # Prefect pipeline design
│   ├── storage-architecture.md     # Hybrid storage design
│   ├── llm-abstraction.md          # LLM provider abstraction
│   └── decisions/                  # Architecture Decision Records (NEW)
│       ├── 001-prefect-over-custom.md
│       ├── 002-langchain-over-litellm.md
│       └── 003-hybrid-storage.md
│
├── features/                       # Feature specifications (keep as-is)
│   ├── mark-command.md
│   ├── collect-command.md
│   ├── cost-tracking.md
│   ├── hybrid-storage.md
│   ├── llm-abstraction.md
│   ├── declarative-pipeline.md
│   └── smart-repo-fetcher.md       # NEW (from Task 3)
│
├── project/                        # Project management (NEW)
│   ├── roadmap.md                  # High-level roadmap
│   ├── phases.md                   # Phase breakdown
│   ├── status.md                   # Current implementation status
│   ├── metrics.md                  # Success metrics & tracking
│   └── history/                    # Historical snapshots (NEW)
│       ├── phase1-complete.md
│       ├── modernization.md
│       └── implementation-summary.md
│
└── deployment/                     # Deployment guides (NEW)
    ├── docker.md                   # Docker deployment (planned)
    ├── cloud.md                    # Cloud deployment (planned)
    └── production.md               # Production checklist (planned)
```

---

## 📋 Migration Plan

### Phase 1: Smart Repo Fetcher Documentation (HIGHEST PRIORITY) (1 hour)
1. Ensure `docs/features/smart-repo-fetcher.md` is complete and up-to-date
2. Create user-facing documentation in `user-guide/smart-fetching.md`
3. Add smart fetcher configuration examples to `user-guide/configuration.md`
4. Update roadmap to reflect Smart Repo Fetcher as Phase 1 priority
5. Create quick reference guide for fetch modes (fast/standard/thorough/exhaustive)

**Rationale**: Smart Repo Fetcher provides immediate value (50-70% cost reduction, 3-5x speedup) and is independent of other features. Prioritizing its documentation ensures users can leverage this optimization immediately.

### Phase 2: Create New Structure (30 minutes)
1. Create new directory structure
2. Create `docs/index.md` as documentation hub
3. Move files to appropriate locations (see mapping below)

### Phase 3: Consolidate Content (2 hours)
1. Merge duplicate content:
   - Combine `LLM_PROVIDERS.md` + `PHASE1_LLM_PROVIDERS.md` → `user-guide/llm-providers.md`
   - Merge status docs → `project/status.md` + archive old ones
   - Extract architecture from `instructions.md` → `design/overview.md`

2. Split large files:
   - `PROJECT_PLAN.md` → `project/roadmap.md` + `project/phases.md`
   - `USAGE.md` → `user-guide/usage.md` + `user-guide/commands.md`

3. Create new content:
   - `docs/index.md` - Documentation hub with clear navigation
   - `user-guide/troubleshooting.md` - Common issues from TODO.md
   - `developer-guide/architecture.md` - High-level system overview
   - `design/decisions/` - Extract decisions from PROJECT_PLAN.md

### Phase 4: Update References (1 hour)
1. Update README.md to link to new structure
2. Update CONTRIBUTING.md to reference developer-guide/
3. Update all internal cross-references
4. Add navigation to each doc (breadcrumbs or links)

### Phase 5: Archive Old Files (15 minutes)
1. Move deprecated files to `docs/project/history/`
2. Add deprecation notices with pointers to new locations
3. Update .gitignore if needed

---

## 🗂️ File Migration Mapping

### To Delete (after content is migrated)
- `PROJECT_SUMMARY.md` → merged into `project/status.md`
- `IMPLEMENTATION_SUMMARY.md` → merged into `project/status.md`
- `MODERNIZATION.md` → archive to `project/history/modernization.md`

### To Move/Rename

| Old Location | New Location | Notes |
|--------------|--------------|-------|
| `docs/USAGE.md` | `docs/user-guide/usage.md` | Split into usage + commands |
| `docs/LLM_PROVIDERS.md` | `docs/user-guide/llm-providers.md` | Merge with PHASE1 version |
| `docs/PHASE1_LLM_PROVIDERS.md` | Archive to `project/history/` | Implementation notes |
| `docs/DECLARATIVE_PIPELINE_DESIGN.md` | `docs/design/pipeline-architecture.md` | Rename for consistency |
| `docs/PROJECT_PLAN.md` | Split → `project/roadmap.md` + `phases.md` | Too large, split by concern |
| `docs/PHASE1_COMPLETE.md` | `docs/project/history/phase1-complete.md` | Archive, historical |
| `instructions.md` | Extract → `design/overview.md` | Keep original as reference |

### To Create (New Content)

| File | Purpose | Priority |
|------|---------|----------|
| `user-guide/smart-fetching.md` | Smart Repo Fetcher user guide | **P0 - Critical (HIGHEST)** |
| `user-guide/fetch-modes.md` | Fetch modes quick reference | **P0 - Critical** |
| `docs/index.md` | Documentation hub | P0 - Critical |
| `user-guide/installation.md` | Extract from README | P1 - High |
| `user-guide/configuration.md` | Config file reference (include smart fetch settings) | P1 - High |
| `user-guide/commands.md` | CLI reference | P1 - High |
| `user-guide/troubleshooting.md` | Common issues | P1 - High |
| `developer-guide/architecture.md` | System architecture | P1 - High |
| `developer-guide/api-reference.md` | Python API docs | P2 - Medium |
| `design/intenthub-principles.md` | IntentHub demonstration | P2 - Medium |
| `design/decisions/*.md` | ADRs for key decisions | P2 - Medium |
| `project/status.md` | Current status (consolidated) | P1 - High |
| `project/metrics.md` | Success metrics tracking | P3 - Low |

---

## 📝 Example: docs/index.md

```markdown
# GitHub Curator Documentation

Welcome to the GitHub Curator documentation!

## 👋 New Here?

- **Users**: Start with the [Quickstart Guide](../QUICKSTART.md), then explore the [User Guide](user-guide/usage.md)
- **Contributors**: Read [Contributing](../CONTRIBUTING.md), then see [Developer Guide](developer-guide/architecture.md)
- **Project Managers**: Check the [Roadmap](project/roadmap.md) and [Current Status](project/status.md)

## 📚 Documentation Sections

### For Users
- **[Smart Fetching Guide](user-guide/smart-fetching.md)** - ⚡ Optimize speed and cost (50-70% savings)
- [Fetch Modes Reference](user-guide/fetch-modes.md) - Fast/Standard/Thorough/Exhaustive modes
- [Installation](user-guide/installation.md) - Setup and prerequisites
- [Configuration](user-guide/configuration.md) - Config file reference
- [Usage Guide](user-guide/usage.md) - Basic to advanced usage
- [CLI Commands](user-guide/commands.md) - Command reference
- [LLM Providers](user-guide/llm-providers.md) - Configure different LLMs
- [Troubleshooting](user-guide/troubleshooting.md) - Common issues
- [Examples](user-guide/examples.md) - Real-world use cases

### For Developers
- [Architecture Overview](developer-guide/architecture.md) - System design
- [Development Setup](developer-guide/development-setup.md) - Dev environment
- [Testing Guide](developer-guide/testing.md) - Running tests
- [API Reference](developer-guide/api-reference.md) - Python API
- [Code Style](developer-guide/code-style.md) - Coding standards

### Design & Architecture
- [Design Overview](design/overview.md) - High-level design
- [IntentHub Principles](design/intenthub-principles.md) - Demonstrated principles
- [Pipeline Architecture](design/pipeline-architecture.md) - Prefect pipeline
- [Storage Architecture](design/storage-architecture.md) - Hybrid storage
- [LLM Abstraction](design/llm-abstraction.md) - Provider abstraction
- [Architecture Decisions](design/decisions/) - ADRs

### Features
- [Feature Specifications](features/) - Detailed feature specs
  - [Mark Command](features/mark-command.md)
  - [Collect Command](features/collect-command.md)
  - [Cost Tracking](features/cost-tracking.md)
  - [Smart Repo Fetcher](features/smart-repo-fetcher.md)

### Project Management
- [Roadmap](project/roadmap.md) - Future plans
- [Phases](project/phases.md) - Phase breakdown
- [Current Status](project/status.md) - Implementation status
- [Success Metrics](project/metrics.md) - Tracking metrics
- [History](project/history/) - Historical snapshots

## 🔗 Quick Links

- [GitHub Repository](https://github.com/IntentHub/github-curator)
- [Issue Tracker](https://github.com/IntentHub/github-curator/issues)
- [Contributing Guide](../CONTRIBUTING.md)
- [Code of Conduct](../CODE_OF_CONDUCT.md) *(if exists)*
```

---

## ✅ Success Criteria

After reorganization, documentation should:

1. **Be discoverable**: Each audience finds their entry point in <30 seconds
2. **No duplication**: Each concept documented in exactly one place
3. **Stay current**: Clear ownership and update paths
4. **Be navigable**: Cross-links and breadcrumbs throughout
5. **Support workflows**: User journey → Developer journey → Project management

---

## 🎯 Benefits

### For Users
- Clear path from installation to advanced usage
- Centralized troubleshooting guide
- Provider-specific setup instructions

### For Contributors
- Architecture overview before diving into code
- Clear testing and development workflows
- Coding standards and API reference

### For Maintainers
- Single source of truth for roadmap and status
- Historical context preserved but separated
- Easy to update without scattered duplicates

### For Everyone
- Documentation hub provides clear navigation
- Consistent structure across all docs
- Version-controlled decision records (ADRs)

---

## ⏱️ Estimated Effort

| Phase | Effort | Can be parallelized? |
|-------|--------|---------------------|
| Phase 1: Smart Repo Fetcher docs | 1 hour | No (highest priority) |
| Phase 2: Create structure | 30 min | No |
| Phase 3: Consolidate content | 2 hours | Yes (by file) |
| Phase 4: Update references | 1 hour | Yes (by doc section) |
| Phase 5: Archive old files | 15 min | No |
| **Total** | **~4.75 hours** | |

---

## 🚀 Next Steps

1. **Review this proposal** with team/maintainers
2. **Get approval** for the new structure
3. **Execute migration** following the phases above
4. **Update TODO.md** to reflect documentation completion
5. **Announce** changes in CHANGELOG.md

---

## 📎 References

- [Current TODO.md](TODO.md) - Lists documentation issues
- [Diátaxis Framework](https://diataxis.fr/) - Documentation system inspiration
- [Write the Docs](https://www.writethedocs.org/) - Documentation best practices
