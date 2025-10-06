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

### ⚠️ Partially Implemented / Missing
- **CLI Commands**: `mark` and `collect` commands were implemented but removed
- **Knowledge Base**: File-based storage only, no semantic search
- **LLM Provider**: Locked to Anthropic Claude
- **Error Detection**: Improved but could be better
- **Documentation**: Scattered across multiple files

### 🚧 Architecture Decisions Made
- **Declarative Pipeline**: Use Prefect for task orchestration ([details](features/declarative-pipeline.md))
- **Hybrid Storage**: File + Vector DB + Graph DB ([details](features/hybrid-storage.md))
- **LLM Abstraction**: Use LangChain for multi-provider support ([details](features/llm-abstraction.md))

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

**Timeline**: 4-6 weeks
**Goal**: Modern, scalable, intelligent curation platform

#### Phase 1: Foundation (Week 1)
**Focus**: Restore features + improve architecture

- [ ] Restore `mark` and `collect` commands
- [ ] Fix error detection (Anthropic/GitHub/generic)
- [ ] Implement LangChain provider abstraction
- [ ] Support multiple LLM providers (Anthropic/OpenAI/Ollama/Google)

**Deliverables**: All original features restored with better error handling

#### Phase 2: Semantic Search (Week 2)
**Focus**: Add vector database for intelligent search

- [ ] Integrate ChromaDB for embeddings
- [ ] Implement semantic repository search
- [ ] Add "find similar repos" functionality
- [ ] Migrate existing knowledge base to vector store

**Deliverables**: Semantic search like "find repos similar to FastAPI"

#### Phase 3: Graph Relationships (Week 3)
**Focus**: Add graph database for pattern discovery

- [ ] Integrate NetworkX for relationship tracking
- [ ] Build topic co-occurrence graph
- [ ] Implement architectural pattern detection
- [ ] Add topic clustering analysis

**Deliverables**: Automatic pattern discovery and topic clustering

#### Phase 4: Unified Knowledge Store (Week 4)
**Focus**: Combine all storage layers with clean API

- [ ] Create `KnowledgeStore` unified API
- [ ] Intelligent query routing (file/vector/graph)
- [ ] Implement hybrid queries
- [ ] Add recommendation system

**Deliverables**: Single API for all knowledge operations

#### Phase 5: Advanced Features (Week 5-6)
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
| `mark` | ⚠️ Missing | P1 | AI-powered topic inference → [Restore plan](features/mark-command.md) |
| `collect` | ⚠️ Missing | P1 | Knowledge base building → [Restore plan](features/collect-command.md) |
| `show` | ✅ Implemented | P2 | Display past curations |
| `setup` | ✅ Implemented | P0 | Environment validation |
| `validate-config` | ✅ Implemented | P2 | Config validation |

### Infrastructure Features

| Feature | Status | Priority | Details |
|---------|--------|----------|---------|
| Declarative Pipeline | 🚧 Phase 1 Done | P0 | → [Pipeline Plan](features/declarative-pipeline.md) |
| Hybrid Storage | 📋 Designed | P1 | → [Storage Plan](features/hybrid-storage.md) |
| LLM Abstraction | 📋 Designed | P1 | → [LLM Plan](features/llm-abstraction.md) |
| Vector Search | 📋 Planned | P1 | Part of hybrid storage |
| Graph DB | 📋 Planned | P2 | Part of hybrid storage |
| RAG Analysis | 📋 Planned | P3 | Future enhancement |

### Quality & DevOps

| Feature | Status | Priority | Details |
|---------|--------|----------|---------|
| Error Detection | 🚧 Improved | P0 | Better cause detection |
| Testing | ⚠️ Minimal | P1 | Need comprehensive suite |
| Documentation | ⚠️ Scattered | P1 | Consolidation needed |
| CI/CD | ❌ Missing | P2 | GitHub Actions |
| Docker | ❌ Missing | P3 | Containerization |

---

## Decision Log

### Recent Architectural Decisions

1. **Prefect for Pipeline** (Oct 2025)
   - **Decision**: Use Prefect instead of custom build system
   - **Rationale**: Production-ready, built-in caching, parallel execution
   - **Result**: 83x speedup on cached runs
   - **Docs**: [PHASE1_COMPLETE.md](PHASE1_COMPLETE.md)

2. **Hybrid Storage** (Oct 2025)
   - **Decision**: File cache + ChromaDB + NetworkX
   - **Rationale**: Balance simplicity, performance, and capabilities
   - **Next**: Implementation in Phase 2-3
   - **Docs**: [features/hybrid-storage.md](features/hybrid-storage.md)

3. **LangChain over LiteLLM** (Oct 2025)
   - **Decision**: Use LangChain for LLM abstraction
   - **Rationale**: Unified ecosystem (LLM + embeddings + vector DB)
   - **Next**: Implementation in Phase 1-2
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

### Open Questions
1. **Deployment**: Self-hosted vs. cloud service?
2. **Pricing**: Free tier limits for embeddings/LLM?
3. **Community**: Accept external contributions?
4. **Data**: Share curated lists publicly?

### Next Decision Points
- [ ] **Week 1**: Choose Option A or B
- [ ] **Week 2**: Embedding provider (OpenAI vs. open source)
- [ ] **Week 3**: Graph DB (NetworkX vs. Neo4j)
- [ ] **Week 4**: RAG implementation strategy

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

**Last Updated**: October 6, 2025
**Status**: Phase 1 Complete, Planning Phase 2
**Next Milestone**: Restore missing commands (Option A) or Begin hybrid storage (Option B)
