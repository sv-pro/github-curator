# Research Architecture Redesign

**Status**: Design Phase
**Date**: 2025-10-11
**Goal**: Redesign curator around time-series topic research workflow

## Problem Statement

Current command structure is confusing with unclear separation between:
- One-off exploration (`curate`)
- Persistent tracking (`track`, `curate-tracked`, `review`)
- Knowledge building (`collect`, `mark`)

User's actual workflow is **time-series research**: tracking how a topic area evolves over time through periodic snapshots and comparison.

## User Workflow

### Meta Flow
1. **Research Setup**: Decide on topic, collect initial repos, baseline evaluation
2. **Publish**: Generate report/post from current state
3. **Periodic Updates**:
   - Topic refresh: discover new repos in the space
   - Repo updates: track changes within existing repos
4. **Re-publish**: Generate update posts showing evolution over time

### Key Requirements
- Track topic evolution (new repos appearing)
- Track repo evolution (changes within repos)
- Compare snapshots over time
- Generate publishable content (blog posts)
- Support multiple concurrent research topics

## Proposed Architecture

### Core Concept: Research Workspaces

Each research topic is a self-contained workspace:

```
~/.github-curator/research/<topic-name>/
├── config.yaml              # Research configuration
├── repos/                   # Tracked repositories (cloned)
│   ├── org1/repo1/
│   │   ├── .curator/
│   │   │   ├── CURATION.md  # Full history
│   │   │   └── REVIEW.md    # Latest state
│   │   └── [repo files...]
│   └── org2/repo2/
├── snapshots/               # Point-in-time evaluations
│   ├── 2025-10-11-baseline.json
│   └── 2025-11-15-update.json
└── reports/                 # Generated content
    ├── 2025-10-11-initial.md
    └── 2025-11-15-update.md
```

### Command Structure

#### 1. Research Management
```bash
curator research init "<name>" --query "<search theme>"
curator research list [topic-name]     # List research topics or repos
curator research show <topic-name>     # Show research details
curator research delete <topic-name>   # Remove research
```

#### 2. Collection Building
```bash
curator research collect <topic> --limit N    # Search, evaluate, add repos
curator research add <topic> <repo-url>...    # Manually add specific repos
curator research remove <topic> <org/repo>    # Remove repo from research
```

#### 3. Evaluation & Snapshots
```bash
curator research snapshot <topic> --name "<label>"
# Creates point-in-time evaluation of all repos
# Updates .curator/CURATION.md for each repo
# Saves snapshot JSON

curator research diff <topic> --from <snap1> --to <snap2>
# Shows changes between snapshots:
# - New repos discovered
# - Repo changes (commits, stars, releases)
# - Trending up/down
```

#### 4. Periodic Updates
```bash
curator research refresh <topic> --sync        # Pull latest code, re-evaluate
curator research refresh <topic> --discover    # Find new repos in space
curator research refresh <topic> --all         # Both sync + discover
```

#### 5. Content Generation
```bash
curator research report <topic> --snapshot <name> --output <file>
# Generate initial report

curator research report <topic> \
  --compare-from <snap1> --compare-to <snap2> \
  --output <file>
# Generate "what's changed" update report
```

## Command Mapping

| Current Command | New Command | Notes |
|-----------------|-------------|-------|
| `curate` | `research collect` | Now persists to research workspace |
| `track` | `research add` | Scoped to research topic |
| `list-tracked` | `research list` | Shows repos in research |
| `curate-tracked` | `research snapshot` | Creates point-in-time evaluation |
| `review` | `research refresh --sync` | Updates all repos in research |
| `collect` | Removed | Merged into `research collect` |
| `mark` | Deferred | Future: `research suggest-topics` |
| `show` | Keep | Shows previous curation results |
| `setup` | Keep | Setup validation |
| `validate-config` | Keep | Config validation |

## Data Structures

### Research Config (config.yaml)
```yaml
name: "python-async-2025"
query: "Modern Python async frameworks and libraries"
created: "2025-10-11T10:00:00Z"
theme:
  focus: "async, frameworks, production-ready"
  exclude: "deprecated, experimental"
search:
  min_stars: 100
  max_age_days: 730
  language: "python"
snapshots:
  - name: "baseline"
    date: "2025-10-11T10:00:00Z"
  - name: "nov-update"
    date: "2025-11-15T10:00:00Z"
```

### Snapshot JSON
```json
{
  "research": "python-async-2025",
  "name": "baseline",
  "created": "2025-10-11T10:00:00Z",
  "query": "Modern Python async frameworks and libraries",
  "repos": [
    {
      "full_name": "fastapi/fastapi",
      "score": 9.2,
      "confidence": 0.85,
      "stars": 75000,
      "last_commit": "2025-10-10T12:00:00Z",
      "dimensions": {
        "production_ready": 9.5,
        "documentation": 9.0,
        "community": 9.8
      },
      "evidence": ["...", "..."],
      "repo_commit": "abc123..."
    }
  ],
  "summary": {
    "total_repos": 18,
    "avg_score": 7.5,
    "top_repos": 5
  }
}
```

## Implementation Phases

### Phase 1: Core Infrastructure (Days 1-2)
**Goal**: Basic research workspace management

- [ ] Create `curator/research/` module
- [ ] `research_manager.py`: Workspace CRUD operations
- [ ] `research init`: Create new research workspace
- [ ] `research list`: List research topics
- [ ] `research add`: Add repos to research (clone to repos/)
- [ ] `research show`: Show research details
- [ ] Config.yaml structure and persistence

**Deliverables**:
- Can create research workspace
- Can add repos to research
- Repos cloned to `research/<topic>/repos/`

### Phase 2: Evaluation & Snapshots (Days 3-5)
**Goal**: Point-in-time evaluation system

- [ ] `snapshot.py`: Snapshot data structure and persistence
- [ ] `research collect`: Search + evaluate + add to research
- [ ] `research snapshot`: Create evaluation snapshot
  - Reuse existing `MetacognitiveEvaluator`
  - Iterate over all repos in research
  - Save snapshot JSON
  - Update each repo's `.curator/CURATION.md`
- [ ] `research refresh --sync`: Pull + re-evaluate all repos

**Deliverables**:
- Can collect repos into research
- Can create named snapshots
- Can update tracked repos

### Phase 3: Discovery & Comparison (Days 6-8)
**Goal**: Time-series analysis

- [ ] `research refresh --discover`: Find new repos
  - Re-run GitHub search
  - Filter out existing repos
  - Evaluate and suggest additions
- [ ] `comparison.py`: Snapshot diff algorithms
- [ ] `research diff`: Compare two snapshots
  - New repos discovered
  - Repo changes (commits, stars)
  - Trending analysis
  - Stale detection

**Deliverables**:
- Can discover new repos in topic space
- Can compare snapshots
- Shows meaningful change detection

### Phase 4: Content Generation (Days 9-11)
**Goal**: Publishing-ready reports

- [ ] `report_generator.py`: LLM-powered content generation
- [ ] `research report`: Generate narrative reports
  - Initial report from single snapshot
  - Update report comparing two snapshots
  - Uses Claude to generate prose
  - Markdown output
- [ ] Report templates and prompts

**Deliverables**:
- Can generate initial report
- Can generate "what's changed" update report
- Human-readable, blog-post ready

### Phase 5: Migration & Polish (Days 12-13)
**Goal**: Clean transition, documentation

- [ ] Deprecation warnings for old commands
- [ ] Migration guide for existing tracked repos
- [ ] Update all documentation
- [ ] Add `research` examples to README
- [ ] CLI help text polish
- [ ] Error messages improvement

**Deliverables**:
- Smooth migration path
- Complete documentation
- All old commands marked deprecated

## Technical Considerations

### Reuse Existing Components
- `IntentStructurer`: For theme → dimensions
- `MetacognitiveEvaluator`: For repo evaluation
- `GitHubAPIClient`: For search and API calls
- `RepositoryAnalyzer`: For repo analysis
- `RepoTracker` git operations: For cloning, pulling

### New Components Needed
- `ResearchManager`: Workspace CRUD
- `SnapshotManager`: Snapshot creation and storage
- `ComparisonEngine`: Diff between snapshots
- `ReportGenerator`: LLM-powered content generation

### Backward Compatibility
- Keep old commands working with deprecation warnings
- Provide migration script: old tracked repos → research workspace
- Config file changes: add `research` section

### Performance
- Bulk operations should be parallelizable
- Cache GitHub search results
- Incremental snapshot updates (only changed repos)

## Success Criteria

1. **User can complete full workflow**:
   - Init research → collect → snapshot → report
   - Refresh → new snapshot → diff → update report

2. **Clear separation of concerns**:
   - Research management vs evaluation vs reporting
   - No confusion about what command to use

3. **Time-series analysis works**:
   - Can track topic evolution over months
   - Meaningful change detection
   - Useful comparison reports

4. **Publishing-ready output**:
   - Generated reports are blog-post quality
   - Minimal manual editing needed

5. **Migration path exists**:
   - Existing users can migrate smoothly
   - Documentation is clear

## Open Questions

1. **Snapshot naming**: User-provided names vs auto-generated timestamps?
   - Proposal: Both - required name + auto timestamp
   - Format: `{timestamp}-{user-name}.json`

2. **Report customization**: How much control over output format?
   - Proposal: Templates + Claude generation
   - User can override templates

3. **Multiple research topics**: How to switch between them?
   - Proposal: Always explicit topic name in command
   - Or: "active" research concept (like git branches)

4. **Snapshot retention**: Keep all forever or prune old ones?
   - Proposal: Keep all, they're just JSON
   - Add `research prune` later if needed

5. **Collaboration**: Should research be git-friendly for sharing?
   - Proposal: Yes - config.yaml and snapshots/ are git-friendly
   - repos/ should be in .gitignore

## Next Steps

1. **Get user approval** on this design
2. **Create feature branch**: `feature/research-architecture`
3. **Start Phase 1 implementation**
4. **Iterate with user feedback**

## References

- Current tracking system: [docs/REPO_TRACKING.md](REPO_TRACKING.md)
- Existing evaluation pipeline: [curator/core/](../curator/core/)
- Smart fetcher: [curator/github/smart_fetcher.py](../curator/github/smart_fetcher.py)
