# GitHub Curator - TODO

**Last Updated**: 2025-10-09
**Current Phase**: Phase 1 Complete, Planning Phase 2

This document tracks the gap between the desired state (as defined in PROJECT_PLAN.md and feature specs) and the current implementation.

---

## ✅ Completed (Phase 1)

### Core Commands
- [x] `curate` command - Main curation workflow
- [x] `mark` command - AI-powered topic inference (restored)
- [x] `collect` command - Knowledge base building (restored)
- [x] `show` command - Display past curations
- [x] `setup` command - Environment validation
- [x] `validate-config` command - Config validation

### Infrastructure
- [x] LLM abstraction layer with factory pattern (curator/llm/)
- [x] Multi-provider support (Anthropic, OpenAI, Google, Ollama)
- [x] Improved error detection (Anthropic vs GitHub vs generic)
- [x] Prefect pipeline foundation (curator/pipeline/)
- [x] Basic knowledge base (curator/knowledge/)
- [x] Adaptive search strategy (curator/github/adaptive_search.py)

---

## 🚧 Phase 2: Smart Repo Fetcher (Current Priority)

**Status**: Not started
**Timeline**: ~1 week
**Priority**: P1 (High Priority)

**Concept**: Avoid brute-force repo analysis through gradual, adaptive fetching:

### Multi-Stage Analysis Strategy

1. **Lightweight Analysis Phase**:
   - Fetch only README.md and root-level docs
   - Check topics list (GitHub API metadata)
   - Look for documentation in doc/, docs/ folders
   - Make initial relevance decision

2. **Decision Point**:
   - If initial analysis shows high relevance → proceed to deep analysis
   - If low relevance → skip (save API calls and time)
   - If uncertain → fetch additional context (ARCHITECTURE.md, examples/)

3. **Deep Analysis Phase** (only if needed):
   - Clone repository (if --use-git-clone)
   - Analyze full code structure
   - Extract architectural patterns
   - Perform comprehensive evaluation

### Implementation Tasks

- [ ] Design multi-stage analysis algorithm
- [ ] Define relevance thresholds for each stage
- [ ] Create `curator/github/smart_fetcher.py`
- [ ] Add confidence-based decision tree
- [ ] Track savings (API calls, time, LLM costs)
- [ ] Add `--smart-fetch` flag to curate command (make default?)
- [ ] Document algorithm and thresholds
- [ ] Create `docs/features/smart-repo-fetcher.md`

**Benefits**:

- Faster curation (skip irrelevant repos early)
- Lower API costs (fewer LLM calls)
- Better GitHub rate limit usage
- Configurable aggressiveness (conservative vs thorough)

**Deliverables**:

- Multi-stage analysis system with adaptive fetching
- Cost and time savings tracking
- Comprehensive feature documentation

---

## 📋 Phase 3: Cost Tracking (Planned)

**Status**: Not started
**Timeline**: ~1 week
**Reference**: docs/features/cost-tracking.md

### Cost Tracking (P1 - High Priority)

- [ ] Create `curator/llm/cost_calculator.py` with provider pricing tables
- [ ] Add token counting to each LLM provider wrapper
- [ ] Track cumulative costs per command execution
- [ ] Display cost summary after commands complete
- [ ] Add cost comparison tips (e.g., "Using Ollama would save $X")
- [ ] Store cost history in `.curator/costs/` directory
- [ ] Add `--show-costs` flag to commands
- [ ] Create cost reporting CLI command: `curator costs [--from DATE] [--to DATE]`

**Deliverables**:

- Cost display after each `curate`, `mark`, `collect` command
- Historical cost tracking and reporting
- Provider cost comparison recommendations

---

## 📋 Phase 4: Semantic Search (Planned)

**Status**: Not started
**Timeline**: ~1 week
**Reference**: docs/features/hybrid-storage.md

### Semantic Search with ChromaDB (P1 - High Priority)

- [ ] Add ChromaDB dependency to pyproject.toml
- [ ] Create `curator/knowledge/vector_store.py` wrapper
- [ ] Generate embeddings during `collect` command
- [ ] Implement semantic search: `curator search "find repos similar to FastAPI"`
- [ ] Add vector storage to KnowledgeBase class
- [ ] Migrate existing knowledge base to ChromaDB (migration script)
- [ ] Use semantic search in `mark` command for better topic suggestions
- [ ] Add `--semantic` flag to collect command

**Deliverables**:

- Semantic search CLI command
- Enhanced topic inference using similarity
- Migration path for existing knowledge bases

---

## 📋 Phase 5: Graph Relationships (Planned)

**Status**: Not started
**Timeline**: ~1 week
**Reference**: docs/features/hybrid-storage.md

### Graph Database with NetworkX

- [ ] Add NetworkX dependency
- [ ] Create `curator/knowledge/graph_store.py`
- [ ] Build topic co-occurrence graph during collection
- [ ] Track repository relationships (forks, dependencies)
- [ ] Implement pattern detection (architectural styles, common combinations)
- [ ] Add topic clustering analysis
- [ ] Create visualization for relationship graphs
- [ ] CLI command: `curator graph [--topic TOPIC] [--repo REPO]`

**Deliverables**:

- Topic relationship discovery
- Architectural pattern detection
- Visual graph exploration

---

## 📋 Phase 6: Unified Knowledge Store (Planned)

**Status**: Not started
**Timeline**: ~1 week
**Reference**: docs/features/hybrid-storage.md

### Hybrid Storage Integration

- [ ] Create unified `KnowledgeStore` API in `curator/knowledge/store.py`
- [ ] Intelligent query routing (file vs vector vs graph)
- [ ] Implement hybrid queries (e.g., "Python repos with async patterns, similar to FastAPI")
- [ ] Add recommendation system
- [ ] Performance benchmarks for different query types
- [ ] Cache layer for frequent queries
- [ ] Background indexing for large knowledge bases

**Deliverables**:

- Single API for all knowledge operations
- Hybrid query support
- Recommendation engine

---

## 📋 Phase 7: Advanced Features (Future)

**Status**: Not started
**Timeline**: ~2 weeks
**Reference**: docs/PROJECT_PLAN.md

### RAG and Conversational Curation

- [ ] Implement RAG for README analysis
- [ ] Add conversational curation mode with memory
- [ ] Context-aware follow-up queries
- [ ] Incremental refinement of curation themes
- [ ] Export curated lists to various formats (CSV, SQL, etc.)
- [ ] Batch curation (multiple themes in parallel)

**Deliverables**:

- Conversational interface
- RAG-enhanced analysis
- Advanced export options

---

## 🧪 Testing & Quality (Ongoing)

**Status**: Minimal coverage
**Priority**: P1 (High)

### Unit Tests
- [ ] Core modules tests (intent_structuring, metacognitive_eval, validation, reflection)
  - [x] Basic intent structuring tests exist
  - [ ] Comprehensive test coverage (target: >80%)
- [ ] GitHub integration tests (api_client, repo_analyzer, adaptive_search)
- [ ] LLM provider tests (all providers, fallback mechanisms)
- [ ] Knowledge base tests (all storage layers)
- [ ] Pipeline tests (Prefect tasks and flows)

### Integration Tests
- [ ] End-to-end curation workflow
- [ ] Multi-provider LLM switching
- [ ] Knowledge base lifecycle (collect → mark → search)
- [ ] Error recovery and retry logic

### Performance Tests
- [ ] Benchmark cache hit rates (target: >80%)
- [ ] Measure evaluation speed (target: <30s for 50 repos with cache)
- [ ] Rate limit handling tests
- [ ] Large knowledge base scalability

**Deliverables**:
- Test coverage >80% for core modules
- CI pipeline running all tests
- Performance benchmarks documented

---

## 📚 Documentation (Ongoing)

**Status**: Scattered across multiple files
**Priority**: P2 (Medium)

### Documentation Organization (see Task 2 in github-curator.todo)
- [ ] Consolidate overlapping documentation files
- [ ] Create clear documentation structure (see proposed schema in Task 2)
- [ ] API documentation (Sphinx or MkDocs)
- [ ] Architecture decision records (ADRs)
- [ ] Deployment guide (Docker, cloud platforms)
- [ ] Troubleshooting guide (common errors, solutions)

### Current Documentation Files
```
Root level (scattered):
├── README.md                      # Main entry point
├── QUICKSTART.md                  # Quick start guide
├── instructions.md                # Original spec (comprehensive)
├── IMPLEMENTATION_SUMMARY.md      # Implementation status
├── PROJECT_SUMMARY.md             # Project overview
├── CONTRIBUTING.md                # Contribution guide
├── CLAUDE.md                      # Claude Code integration
└── MODERNIZATION.md               # Modernization plan

docs/:
├── PROJECT_PLAN.md                # Roadmap and planning
├── USAGE.md                       # Usage guide
├── PHASE1_COMPLETE.md             # Phase 1 summary
├── PHASE1_LLM_PROVIDERS.md        # LLM provider docs
├── LLM_PROVIDERS.md               # LLM provider guide
├── DECLARATIVE_PIPELINE_DESIGN.md # Pipeline architecture
└── features/                      # Feature-specific docs
    ├── mark-command.md
    ├── collect-command.md
    ├── cost-tracking.md
    ├── hybrid-storage.md
    ├── llm-abstraction.md
    └── declarative-pipeline.md
```

**Issues**:
- Duplication between root and docs/ directories
- Multiple "status" documents (IMPLEMENTATION_SUMMARY, PROJECT_SUMMARY, PHASE1_COMPLETE)
- Unclear which document is authoritative
- Missing: API docs, troubleshooting, deployment guide

---

## 🔧 DevOps & Infrastructure

**Status**: Missing
**Priority**: P2 (Medium)

### CI/CD Pipeline
- [ ] GitHub Actions workflow for tests
- [ ] Automated linting (black, ruff, mypy)
- [ ] Type checking in CI
- [ ] Code coverage reporting (codecov.io)
- [ ] Automated release workflow
- [ ] Dependency security scanning (Dependabot)

### Containerization
- [ ] Dockerfile for production
- [ ] docker-compose.yml for local development
- [ ] Multi-stage builds for smaller images
- [ ] Docker Hub or GitHub Container Registry
- [ ] Kubernetes deployment manifests (optional)

### Monitoring & Observability
- [ ] Structured logging (JSON format)
- [ ] Telemetry for LLM calls (costs, latency)
- [ ] Error tracking (Sentry integration)
- [ ] Performance monitoring
- [ ] Usage analytics (privacy-preserving)

---

## ✨ New Features (From github-curator.todo)

### Smart GitHub Repo Fetcher (Task 3)
**Status**: Not designed
**Priority**: P2 (Medium)

**Concept**: Avoid brute-force repo analysis through gradual, adaptive fetching:

1. **Lightweight Analysis Phase**:
   - Fetch only README.md and root-level docs
   - Check topics list (GitHub API metadata)
   - Look for documentation in doc/, docs/ folders
   - Make initial relevance decision

2. **Decision Point**:
   - If initial analysis shows high relevance → proceed to deep analysis
   - If low relevance → skip (save API calls and time)
   - If uncertain → fetch additional context (ARCHITECTURE.md, examples/)

3. **Deep Analysis Phase** (only if needed):
   - Clone repository (if --use-git-clone)
   - Analyze full code structure
   - Extract architectural patterns
   - Perform comprehensive evaluation

**Implementation Tasks**:
- [ ] Design multi-stage analysis algorithm
- [ ] Define relevance thresholds for each stage
- [ ] Create `curator/github/smart_fetcher.py`
- [ ] Add confidence-based decision tree
- [ ] Track savings (API calls, time, LLM costs)
- [ ] Add `--smart-fetch` flag to curate command (make default?)
- [ ] Document algorithm and thresholds

**Benefits**:
- Faster curation (skip irrelevant repos early)
- Lower API costs (fewer LLM calls)
- Better GitHub rate limit usage
- Configurable aggressiveness (conservative vs thorough)

**Reference Document**:
- [ ] Create `docs/features/smart-repo-fetcher.md`

---

## 🐛 Known Issues & Bugs

### Critical
- None currently identified

### High Priority
- [ ] Mark command uses direct Anthropic client instead of LLM factory (curator/__main__.py:485-515)
  - Should use `LLMFactory` for consistency and multi-provider support
- [ ] Config validation doesn't check LLM provider settings
- [ ] No retry logic for transient GitHub API errors (only rate limits)

### Medium Priority
- [ ] Large README files (>50KB) cause slow analysis
- [ ] No progress indicator for long-running operations
- [ ] Error messages don't always show actionable solutions
- [ ] Knowledge base doesn't handle concurrent writes

### Low Priority
- [ ] CLI help text could be more descriptive
- [ ] No shell completion (bash/zsh/fish)
- [ ] Color output not configurable (always enabled)

---

## 📊 Success Metrics (from PROJECT_PLAN.md)

### Technical Metrics
- [ ] **Performance**: <30s for 50 repo curation with cache (not measured yet)
- [ ] **Cache Hit Rate**: >80% on repeated queries (not measured yet)
- [ ] **Accuracy**: >0.7 precision in repo relevance (not measured yet)
- [ ] **Test Coverage**: >80% for core modules (currently <20%)

### User Experience
- [x] **Setup Time**: <5 minutes from clone to first curation ✅
- [ ] **Documentation**: All features documented with examples (gaps exist)
- [x] **Error Messages**: Clear, actionable troubleshooting ✅
- [x] **Query Quality**: Natural language queries work well ✅

### Code Quality
- [ ] **Test Coverage**: >80% for core modules (currently minimal)
- [ ] **Type Coverage**: 100% for public APIs (not enforced)
- [ ] **Linting**: All checks passing (not in CI)
- [x] **Documentation**: All modules have docstrings ✅

---

## 🎯 Immediate Next Steps (Priority Order)

1. **Phase 2 - Smart Repo Fetcher** (1 week)
   - Design multi-stage analysis algorithm
   - Implement adaptive fetching strategy
   - Track cost and time savings

2. **Fix mark command LLM provider** (1 day)
   - Use LLMFactory instead of direct Anthropic client
   - Add provider configuration support

3. **Phase 3 - Cost Tracking** (1 week)
   - Implement cost calculator
   - Add token tracking to all LLM providers
   - Display costs after commands

4. **Phase 4 - Semantic Search** (1 week)
   - Integrate ChromaDB
   - Add embedding generation
   - Implement semantic search command

5. **Testing Foundation** (3 days)
   - Set up CI pipeline
   - Increase test coverage to >50%
   - Add integration tests

6. **Documentation Cleanup** (2 days)
   - Consolidate documentation (see Task 2 proposal)
   - Remove duplicates
   - Clear entry points for different audiences

---

## 📝 Notes

### Decision Points
- **Phase 2 vs Testing**: Start Phase 2 (Smart Repo Fetcher) or focus on testing first?
  - **Recommendation**: Start Smart Repo Fetcher (high performance impact), add tests incrementally
- **Documentation consolidation**: Do it now or after Phase 2-4?
  - **Recommendation**: Do basic cleanup now, comprehensive overhaul after Phase 4

### Open Questions
1. Should smart repo fetcher be opt-in (--smart-fetch) or default behavior?
2. Which embedding provider for ChromaDB? (OpenAI, sentence-transformers, Anthropic)
3. Deploy as CLI-only or add web UI eventually?
4. Public knowledge base sharing - yes/no?

### Reference Documents
- Overall roadmap: `docs/PROJECT_PLAN.md`
- Feature specs: `docs/features/*.md`
- Original spec: `instructions.md`
- Current status: `IMPLEMENTATION_SUMMARY.md`

---

**Auto-generated from**: `docs/PROJECT_PLAN.md`, code analysis, and `github-curator.todo`
**Maintenance**: Update this file as features are completed or priorities change
