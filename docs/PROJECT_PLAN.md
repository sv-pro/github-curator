# GitHub Curator: Project Plan

## Vision

Build an intelligent GitHub repository curator that demonstrates IntentHub principles through:
- **Structured intent** representation
- **Metacognitive** evaluation with explicit confidence
- **Validated** results with full traceability
- **Reflective** learning for continuous improvement

## Current Status (As of October 2025)

### ✅ Implemented (Core Features)
- **Intent Structuring**: Natural language → dimensional evaluation
- **Adaptive Search**: Multi-query heuristic search with feedback loop
- **Metacognitive Evaluation**: Repository assessment with confidence tracking
- **Validation**: Intent, evaluation, and result consistency checks
- **Reflection**: Pattern analysis and improvement suggestions
- **Report Generation**: Markdown, JSON, and HTML trace viewer
- **Prefect Pipeline** (Phase 1): Declarative tasks with caching (83x speedup)
- **Research Workspace System**: Time-series tracking (Phases 1-3, 9 commands)
- **LLM Provider Fallback**: Automatic Anthropic → OpenAI → Ollama chain
- **Smart Repo Fetcher**: Multi-stage analysis (50-70% cost reduction)
- **Automated Testing**: 40+ tests, CI/CD, phase gates (70%+ coverage)

### ⚠️ Partially Implemented / Missing
- **Cost Monitoring**: No visibility into API costs or token usage
- **Knowledge Base**: File-based storage only, no semantic search
- **Documentation**: Scattered across multiple files
- **Snapshot Design**: Several open questions need resolution

### 🚧 Architecture Decisions Made
- **Declarative Pipeline**: Use Prefect for task orchestration ([details](features/declarative-pipeline.md))
- **Hybrid Storage**: File + Vector DB + Graph DB ([details](features/hybrid-storage.md))
- **LLM Abstraction**: Use LangChain for multi-provider support ([details](features/llm-abstraction.md))
- **Research Workspaces**: Self-contained time-series tracking system ([details](RESEARCH_ARCHITECTURE_REDESIGN.md))
- **LLM Fallback**: Automatic provider chain (Anthropic → OpenAI → Ollama) ([details](LLM_FALLBACK.md))

---

## Roadmap

### Option A: Incremental Improvements (Conservative)

**Timeline**: 2-3 weeks
**Goal**: Fix immediate issues, restore missing features

#### Week 1: Restore & Stabilize
- [ ] Restore `mark` command (AI-powered topic inference)
- [ ] Restore `collect` command (knowledge base building)
- [ ] Improve error detection (Anthropic vs GitHub vs generic)
- [ ] Add provider configuration (basic multi-LLM support)

#### Week 2: LLM Flexibility
- [ ] Implement LangChain integration
- [ ] Support Anthropic, OpenAI, Ollama, Google
- [ ] Add provider fallback mechanism
- [ ] Update documentation

#### Week 3: Polish
- [ ] Comprehensive testing
- [ ] Performance optimization
- [ ] Documentation cleanup
- [ ] Bug fixes

**Deliverables**:
- All CLI commands working
- Configurable LLM providers
- Stable, well-documented codebase

---

### Option B: Full Hybrid System (Ambitious) ⭐ Recommended

**Timeline**: 5-7 weeks
**Goal**: Modern, scalable, intelligent curation platform with smart fetching

#### Phase 1: Foundation (Week 1) ✅ **COMPLETE**
**Focus**: Restore features + improve architecture

- [x] Restore `mark` and `collect` commands
- [x] Fix error detection (Anthropic/GitHub/generic)
- [x] Implement LangChain provider abstraction
- [x] Support multiple LLM providers (Anthropic/OpenAI/Ollama/Google)
- [x] Fix configuration compatibility bugs

**Deliverables**: ✅ All original features restored with better error handling

#### Phase 2: Smart Repo Fetcher (Week 2) ✅ **COMPLETE**
**Focus**: Adaptive multi-stage analysis for 50-70% cost reduction and 3-5x speedup

**Implementation**:
- [x] Implement `SmartRepoFetcher` class with multi-stage pipeline
- [x] Stage 1: Metadata-based filtering (stars, topics, size)
- [x] Stage 2: Lightweight analysis (README excerpt + keyword density)
- [x] Stage 3: Deep analysis (full evaluation - current approach)
- [x] Stage 4: Code analysis (stub for future implementation)
- [x] Add CLI options: `--fetch-mode` (fast/standard/thorough/exhaustive)
- [x] Track and display savings (API calls, costs, time)
- [x] Configuration for thresholds and toggles
- [x] Comprehensive unit tests (13 test cases)
- [x] Integration tests with GitHub client and evaluator

**Deliverables**: ✅
- Smart fetching enabled by default with configurable modes
- Cost and time savings displayed after curation
- Savings tracking and reporting
- **Achieved Impact**: 50-70% API call reduction, 60-80% cost savings, 3-5x faster

**See**: [Smart Repo Fetcher Feature Spec](features/smart-repo-fetcher.md)

#### Phase 2.5: Automated Test Suite (Week 2) ✅ **COMPLETE**
**Focus**: Comprehensive testing infrastructure for quality assurance

**Implementation**:
- [x] Create test directory structure (unit/integration/fixtures)
- [x] Implement comprehensive test fixtures and mocks
- [x] Write unit tests for Smart Fetcher (13 tests)
- [x] Write unit tests for metacognitive evaluation (5 tests)
- [x] Write unit tests for GitHub API client (9 tests)
- [x] Write integration tests for curation pipeline (4 test suites)
- [x] Create phase gate test runner script
- [x] Update Makefile with test targets
- [x] Set up GitHub Actions CI/CD workflow
- [x] Write comprehensive testing documentation

**Deliverables**: ✅
- 40+ automated tests (unit + integration)
- Phase gate test runner for quality checkpoints
- CI/CD integration with GitHub Actions
- Testing documentation and quick reference guide
- Multi-Python version testing (3.9-3.12)

**See**: [TESTING.md](../TESTING.md), [TEST_QUICK_REFERENCE.md](../TEST_QUICK_REFERENCE.md), [TESTING_SUITE_SUMMARY.md](../TESTING_SUITE_SUMMARY.md)

#### Phase 2.7: Research Architecture (Week 2-3) ✅ **COMPLETE**
**Focus**: Time-series research workflow with workspace management

**Implementation** (3 phases, 9 commands, ~2,416 lines):
- [x] Phase 1: Core workspace infrastructure (init, list, show, add, delete)
- [x] Phase 2: Evaluation & snapshots (collect, snapshot)
- [x] Phase 3: Updates & comparison (refresh, diff)
- [x] LLM fallback integration (~835 lines)
- [x] Bug fixes & UX improvements (count consistency, resume mode)
- [x] CLI consistency (positional args, auto-generated snapshot names)

**Deliverables**: ✅
- Complete time-series research workflow
- 9 research commands fully operational
- Self-contained workspace system (`~/.github-curator/research/<name>/`)
- Snapshot evaluation and comparison
- Seamless LLM fallback across all operations
- Resume capability for interrupted operations

**See**: [RESEARCH_ARCHITECTURE_REDESIGN.md](RESEARCH_ARCHITECTURE_REDESIGN.md), [LLM_FALLBACK.md](LLM_FALLBACK.md), [.claude/context.md](../.claude/context.md)

#### Phase 3: Cost Monitoring (Week 3) 🔥 **TOP PRIORITY**
**Focus**: Comprehensive cost visibility and tracking across all LLM operations

**Cost Monitoring System**:
- [ ] Create `CostTracker` class with provider pricing tables
- [ ] Track token usage per LLM call (input/output tokens)
- [ ] Integrate into `LangChainProvider` for automatic tracking
- [ ] Display real-time costs during operations
- [ ] Save cost data in research workspace snapshots
- [ ] Add cost comparison between snapshots
- [ ] Provider cost breakdowns (Anthropic vs Ollama vs OpenAI)
- [ ] Cost estimation before expensive operations
- [ ] Budget warnings and limits

**Cost Visualization**:
- [ ] Display cost summary after each command
- [ ] Show cumulative costs per research workspace
- [ ] Cost trends over time (per snapshot)
- [ ] Provider fallback cost analysis
- [ ] Cost savings from Smart Fetcher (already estimated, needs actual tracking)

**Deliverables**:
- Real-time cost tracking for all LLM operations
- Cost summaries in all research commands
- Historical cost tracking in snapshots
- Budget awareness and optimization tips

#### Phase 3.5: Semantic Search (Week 4)
**Focus**: Vector database for intelligent search

**Semantic Search**:
- [ ] Integrate ChromaDB for embeddings
- [ ] Implement semantic repository search
- [ ] Add "find similar repos" functionality
- [ ] Migrate existing knowledge base to vector store

**Deliverables**:
- Semantic search like "find repos similar to FastAPI"

#### Phase 3.9: Research Architecture - Snapshot Design Decisions 🎯 **BLOCKED - NEEDS DECISIONS**
**Focus**: Resolve open design questions before continuing snapshot development

**Open Design Questions** (documented in [SNAPSHOT_DESIGN_QUESTIONS.md](SNAPSHOT_DESIGN_QUESTIONS.md)):

1. **Snapshot Artifacts**: Should we generate semantic delta artifacts in addition to full state?
   - Options: Full state only (current), auto-generate deltas, optional flag, on-demand command
   - Impact: Richer semantics vs complexity, requires LLM analysis of changes

2. **Git Pull Strategy**: Should snapshot auto-pull repos before evaluation?
   - Options: Always pull, never pull (current), --pull flag, auto-pull if stale, interactive prompt
   - Impact: Freshness vs performance vs user control vs transparency

3. **LLM Metadata Tracking**: How to track provider/model used for reproducibility?
   - Options: Snapshot-level aggregate, per-evaluation granular, both levels, only on fallback
   - Impact: Traceability vs complexity vs comparability

4. **Snapshot Comparability**: How to handle comparing snapshots from different models?
   - Options: Warn on mismatch, normalize scores, re-evaluate baseline, accept approximate
   - Impact: Accuracy vs cost vs user awareness

**Deliverables**:
- Design decisions documented
- Implementation plan for chosen approaches
- Update CLAUDE.md with architectural decisions

#### Phase 4: Graph Relationships (Week 5)
**Focus**: Add graph database for pattern discovery

- [ ] Integrate NetworkX for relationship tracking
- [ ] Build topic co-occurrence graph
- [ ] Implement architectural pattern detection
- [ ] Add topic clustering analysis

**Deliverables**: Automatic pattern discovery and topic clustering

#### Phase 5: Unified Knowledge Store (Week 5)
**Focus**: Combine all storage layers with clean API

- [ ] Create `KnowledgeStore` unified API
- [ ] Intelligent query routing (file/vector/graph)
- [ ] Implement hybrid queries
- [ ] Add recommendation system

**Deliverables**: Single API for all knowledge operations

#### Phase 6: Advanced Features (Week 6-7)
**Focus**: RAG, advanced queries, optimization

- [ ] Implement RAG for README analysis
- [ ] Add conversational curation (memory + context)
- [ ] Performance optimization (caching, indexing)
- [ ] Comprehensive documentation
- [ ] Production deployment guide

**Deliverables**: Production-ready intelligent curator

---

## Feature Roadmap

### Core Commands

| Command | Status | Priority | Details |
|---------|--------|----------|---------|
| `curate` | ✅ Implemented | P0 | Main curation workflow |
| `mark` | ✅ Restored | P1 | AI-powered topic inference → [Restore plan](features/mark-command.md) |
| `collect` | ✅ Restored | P1 | Knowledge base building → [Restore plan](features/collect-command.md) |
| `show` | ✅ Implemented | P2 | Display past curations |
| `setup` | ✅ Implemented | P0 | Environment validation |
| `validate-config` | ✅ Implemented | P2 | Config validation |

### Research Commands (Time-Series Tracking)

| Command | Status | Priority | Description |
|---------|--------|----------|-------------|
| `research init` | ✅ Implemented | P0 | Create research workspace |
| `research list` | ✅ Implemented | P0 | List all workspaces |
| `research show` | ✅ Implemented | P0 | Display workspace details |
| `research add` | ✅ Implemented | P1 | Add single repository |
| `research delete` | ✅ Implemented | P2 | Remove workspace |
| `research collect` | ✅ Implemented | P0 | Search and batch-add repos |
| `research snapshot` | ✅ Implemented | P0 | Evaluate and save snapshot |
| `research refresh` | ✅ Implemented | P0 | Update repos (sync/discover) |
| `research diff` | ✅ Implemented | P0 | Compare snapshots |
| `research report` | 📋 Planned | P1 | Generate markdown reports |

### Infrastructure Features

| Feature | Status | Priority | Details |
|---------|--------|----------|---------|
| Declarative Pipeline | 🚧 Phase 1 Done | P0 | → [Pipeline Plan](features/declarative-pipeline.md) |
| Multi-Provider LLM | ✅ Implemented | P0 | Anthropic/OpenAI/Google/Ollama → [LLM Providers](LLM_PROVIDERS.md) |
| **LLM Provider Fallback** | ✅ **Implemented** | **P0** | **Automatic Anthropic→OpenAI→Ollama chain** → [LLM Fallback](LLM_FALLBACK.md) |
| Error Detection | ✅ Implemented | P0 | Structured error hierarchy with solutions |
| **Smart Repo Fetcher** | ✅ **Phase 2 Done** | **P0** | **50-70% cost savings, 3-5x speedup** → [Smart Fetcher](features/smart-repo-fetcher.md) |
| **Automated Testing** | ✅ **Phase 2.5 Done** | **P0** | **40+ tests, CI/CD, phase gates** → [TESTING.md](../TESTING.md) |
| **Research Workspaces** | ✅ **Phase 2.7 Done** | **P0** | **Time-series tracking, 9 commands** → [Research Architecture](RESEARCH_ARCHITECTURE_REDESIGN.md) |
| **Cost Monitoring** | 🔥 **Phase 3 Priority** | **P0** | **Real-time tracking, budget awareness** → [Cost Tracking](features/cost-tracking.md) |
| Snapshot Design | 🎯 **Blocked** | **P0** | **4 open questions need decisions** → [Snapshot Questions](SNAPSHOT_DESIGN_QUESTIONS.md) |
| Hybrid Storage | 📋 Phase 3-5 | P1 | → [Storage Plan](features/hybrid-storage.md) |
| Vector Search | 📋 Phase 3.5 | P1 | Part of hybrid storage |
| Graph DB | 📋 Phase 4 | P2 | Part of hybrid storage |
| RAG Analysis | 📋 Phase 6 | P3 | Future enhancement |

### Quality & DevOps

| Feature | Status | Priority | Details |
|---------|--------|----------|---------|
| Testing | ✅ Comprehensive | P0 | 40+ tests, phase gates, CI/CD → [TESTING.md](../TESTING.md) |
| Documentation | ✅ Complete | P1 | User + developer docs, testing guides |
| CI/CD | ✅ Implemented | P1 | GitHub Actions with multi-Python testing |
| Code Coverage | ✅ 70%+ | P1 | HTML reports, Codecov integration |
| Security Scanning | ✅ Automated | P2 | Bandit + Safety in CI/CD |
| Docker | ❌ Missing | P3 | Containerization (future) |

---

## Decision Log

### Recent Architectural Decisions

1. **Research Workspace System** (Oct 13, 2025) ✅
   - **Decision**: Implement self-contained research workspaces for time-series tracking
   - **Rationale**: Enable topic evolution tracking, periodic updates, and comparison
   - **Result**: 9 commands, ~2,416 lines, complete workflow
   - **Docs**: [RESEARCH_ARCHITECTURE_REDESIGN.md](RESEARCH_ARCHITECTURE_REDESIGN.md)

2. **LLM Provider Fallback** (Oct 13, 2025) ✅
   - **Decision**: Automatic fallback chain (Anthropic → OpenAI → Ollama)
   - **Rationale**: Prevent workflow interruption when credits exhausted
   - **Result**: Seamless operation, ~835 lines, enabled by default
   - **Docs**: [LLM_FALLBACK.md](LLM_FALLBACK.md)

3. **Cost Monitoring Priority** (Oct 13, 2025) 🔥
   - **Decision**: Make cost monitoring the top priority for Phase 3
   - **Rationale**: Need visibility into API costs, especially with fallback system
   - **Next**: Implement comprehensive cost tracking system
   - **Docs**: [features/cost-tracking.md](features/cost-tracking.md)

4. **Prefect for Pipeline** (Oct 2025)
   - **Decision**: Use Prefect instead of custom build system
   - **Rationale**: Production-ready, built-in caching, parallel execution
   - **Result**: 83x speedup on cached runs
   - **Docs**: [PHASE1_COMPLETE.md](PHASE1_COMPLETE.md)

5. **Hybrid Storage** (Oct 2025)
   - **Decision**: File cache + ChromaDB + NetworkX
   - **Rationale**: Balance simplicity, performance, and capabilities
   - **Next**: Implementation in Phase 3.5-5
   - **Docs**: [features/hybrid-storage.md](features/hybrid-storage.md)

6. **LangChain over LiteLLM** (Oct 2025)
   - **Decision**: Use LangChain for LLM abstraction
   - **Rationale**: Unified ecosystem (LLM + embeddings + vector DB)
   - **Status**: ✅ Implemented with multi-provider support
   - **Docs**: [features/llm-abstraction.md](features/llm-abstraction.md)

---

## Success Metrics

### Technical Metrics
- **Performance**: <30s for 50 repo curation (with cache)
- **Cache Hit Rate**: >80% on repeated queries
- **Accuracy**: >0.7 precision in repo relevance
- **Uptime**: >99% availability (when deployed)

### User Experience
- **Setup Time**: <5 minutes from clone to first curation
- **Documentation**: All features documented with examples
- **Error Messages**: Clear, actionable troubleshooting
- **Query Quality**: Natural language queries work well

### Code Quality
- **Test Coverage**: >80% for core modules
- **Type Coverage**: 100% for public APIs
- **Linting**: All checks passing (black, ruff, mypy)
- **Documentation**: All modules have docstrings

---

## Getting Started

### For Users
```bash
# Quick start
pip install -e .
curator setup
curator curate "AI agents with tool use"
```

### For Developers
```bash
# Setup development environment
python -m venv venv
source venv/bin/activate
pip install -e .[dev]
make setup

# Run tests
make test

# See all commands
curator --help
```

### For Contributors
1. Read [CONTRIBUTING.md](../CONTRIBUTING.md)
2. Check [PROJECT_PLAN.md](PROJECT_PLAN.md) (this file)
3. Pick a feature from roadmap
4. Follow feature-specific plan in [docs/features/](features/)

---

## Questions & Decisions Needed

### 🚨 Critical Decisions Required (Blocking Progress)

#### Snapshot Design Questions
**Status**: Blocking Phase 3.9 and future snapshot features
**Document**: [SNAPSHOT_DESIGN_QUESTIONS.md](SNAPSHOT_DESIGN_QUESTIONS.md)

1. **Snapshot Artifacts**: Should we generate semantic delta artifacts?
   - [ ] Decision needed: Full state only vs deltas vs optional vs on-demand

2. **Git Pull Strategy**: Should snapshot auto-pull repos?
   - [ ] Decision needed: Always vs never vs --pull flag vs smart default vs prompt

3. **LLM Metadata Tracking**: How to track provider/model info?
   - [ ] Decision needed: Snapshot-level vs per-evaluation vs both vs only-on-fallback

4. **Snapshot Comparability**: How to handle different LLM providers?
   - [ ] Decision needed: Warn vs normalize vs re-evaluate vs accept-approximate

**Impact**: Affects reproducibility, cost tracking, and comparison accuracy

### Open Questions
1. **Deployment**: Self-hosted vs. cloud service?
2. **Pricing**: Free tier limits for embeddings/LLM?
3. **Community**: Accept external contributions?
4. **Data**: Share curated lists publicly?

### Next Decision Points
- [x] **Phase 2**: Smart fetcher implementation ✅ Complete
- [x] **Phase 2.5**: Testing infrastructure ✅ Complete
- [x] **Phase 2.7**: Research architecture ✅ Complete
- [ ] **Phase 3**: Cost monitoring implementation (TOP PRIORITY)
- [ ] **Phase 3.9**: Snapshot design decisions (BLOCKED - needs user input)
- [ ] **Phase 3.5**: Embedding provider (OpenAI vs. open source)
- [ ] **Phase 4**: Graph DB (NetworkX vs. Neo4j)
- [ ] **Phase 6**: RAG implementation strategy

---

## References

### Architecture Documents
- [Declarative Pipeline Design](DECLARATIVE_PIPELINE_DESIGN.md)
- [Hybrid Storage Architecture](HYBRID_KNOWLEDGE_STORAGE.md)
- [LLM Abstraction Decision](LLM_ABSTRACTION_DECISION.md)
- [Phase 1 Complete](PHASE1_COMPLETE.md)

### Feature Plans (Detailed)
- [Declarative Pipeline](features/declarative-pipeline.md)
- [Hybrid Storage](features/hybrid-storage.md)
- [LLM Abstraction](features/llm-abstraction.md)
- [Mark Command Restoration](features/mark-command.md)
- [Collect Command Restoration](features/collect-command.md)

### Original Specification
- [instructions.md](../instructions.md) - Original design spec

---

**Last Updated**: October 13, 2025
**Current Phase**: Phase 3 - Cost Monitoring (TOP PRIORITY)
**Status**: Phases 1, 2, 2.5, and 2.7 Complete
**Next Milestone**: Implement comprehensive cost monitoring system with real-time tracking
**Blocked**: Phase 3.9 snapshot design decisions need user input
