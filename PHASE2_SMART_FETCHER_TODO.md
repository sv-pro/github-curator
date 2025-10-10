# Phase 2: Smart Repo Fetcher - Implementation Checklist

**Branch**: `feature/smart-repo-fetcher`
**Started**: 2025-10-10
**Timeline**: 5-7 days
**Priority**: P0 - HIGHEST PRIORITY
**Expected Impact**: 50-70% cost reduction, 60-80% cost savings, 3-5x speedup

---

## 📋 Implementation Progress

### Day 1: Foundation & Core Classes (2-3 hours)

#### Setup & Exploration
- [x] Create feature branch `feature/smart-repo-fetcher`
- [x] Create this implementation checklist
- [ ] Review existing curation pipeline code
- [ ] Identify integration points in `curator/__main__.py`
- [ ] Review existing repo analysis flow in `curator/github/repo_analyzer.py`

#### Core Data Structures
- [ ] Create `curator/github/smart_fetcher.py`
- [ ] Define `Decision` enum (SKIP, CONTINUE_STANDARD, CONTINUE_DEEP)
- [ ] Create `StageResult` dataclass
  - decision: Decision
  - confidence: float
  - reasoning: str
  - cost_saved: float
  - data_fetched: dict
- [ ] Create `AnalysisTrace` class for tracking analysis path
  - repo: str
  - thoroughness: str
  - stages: List[StageResult]
  - fast_tracked: bool
  - total_savings: dict

#### SmartRepoFetcher Class Structure
- [ ] Create `SmartRepoFetcher` class
- [ ] Implement `__init__` with config, intent, github_client, llm_provider
- [ ] Add configuration loading from config
- [ ] Create method stubs for all 4 stages
- [ ] Add `analyze()` main method orchestration

---

### Day 2: Stage 1 & Stage 2 Implementation (3-4 hours)

#### Stage 1: Metadata Filtering
- [ ] Implement `stage1_metadata_check(repo: SearchResult) -> StageResult`
- [ ] Extract keywords from intent dimensions
- [ ] Check stars threshold (configurable multiplier)
- [ ] Check repository size (min/max bounds)
- [ ] Check topics overlap with keywords
- [ ] Check name/description for keywords
- [ ] Calculate metadata score (0-1)
- [ ] Return StageResult with decision
- [ ] Add logging for skipped repos

#### Stage 2: Lightweight Analysis
- [ ] Implement `stage2_lightweight_analysis(repo: SearchResult) -> StageResult`
- [ ] Fetch README excerpt (first 500 lines or 50KB)
- [ ] Calculate keyword density in README
- [ ] Calculate topic overlap score
- [ ] Implement `_calculate_keyword_density()` helper
- [ ] Implement quick LLM check for uncertain cases (0.3-0.7 range)
- [ ] Create `_quick_llm_check()` using cheap model (Haiku)
- [ ] Combine scores and make decision
- [ ] Return StageResult with reasoning

#### Helper Methods
- [ ] Implement `_extract_keywords(intent)` from dimensions
- [ ] Implement `_estimate_savings(stage)` for cost calculation
- [ ] Implement `_calculate_keyword_density(text, keywords)`

---

### Day 3: Stage 3, Stage 4 & Integration (4-5 hours)

#### Stage 3: Deep Analysis (Existing Approach)
- [ ] Implement `stage3_deep_analysis(repo: SearchResult) -> StageResult`
- [ ] Call existing full evaluation flow
- [ ] Wrap existing evaluation in StageResult
- [ ] Track API calls and costs
- [ ] Return evaluation report

#### Stage 4: Code Analysis (Optional)
- [ ] Implement `stage4_code_analysis(repo, evaluation) -> StageResult`
- [ ] Check if cloning is needed (`_should_clone()` helper)
- [ ] Clone repository if needed
- [ ] Analyze code structure
- [ ] Enhance evaluation with code-derived evidence
- [ ] Update confidence scores

#### Analysis Orchestration
- [ ] Implement main `analyze()` method
- [ ] Create AnalysisTrace at start
- [ ] Call stages sequentially based on thoroughness
- [ ] Handle early exits (SKIP decisions)
- [ ] Handle fast-tracking (CONTINUE_DEEP)
- [ ] Save trace for later analysis
- [ ] Return evaluation or None

#### Savings Calculator
- [ ] Create `_calculate_total_savings()` method
- [ ] Track API calls saved
- [ ] Estimate costs saved (by LLM calls avoided)
- [ ] Calculate time saved
- [ ] Return savings summary dict

---

### Day 4: Configuration & CLI Integration (3-4 hours)

#### Configuration File
- [ ] Add `smart_fetch` section to `config/curator.yaml`
- [ ] Define `enabled: true` toggle
- [ ] Add Stage 1 settings (min_stars_multiplier, size bounds)
- [ ] Add Stage 2 settings (quick_model, thresholds, readme_max_lines)
- [ ] Add Stage 3/4 settings (clone thresholds)
- [ ] Define thoroughness presets (fast, standard, thorough, exhaustive)
- [ ] Add example configurations with comments

#### CLI Options
- [ ] Add `--fetch-mode` option to `curate` command
  - Choices: fast, standard, thorough, exhaustive
  - Default: standard
- [ ] Add `--disable-smart-fetch` flag for brute-force mode
- [ ] Update CLI help text with descriptions
- [ ] Add validation for fetch mode options

#### Integration with Curate Command
- [ ] Modify `curator/__main__.py` curate command
- [ ] Initialize SmartRepoFetcher or BruteForceFetcher based on flag
- [ ] Pass thoroughness level from CLI
- [ ] Replace direct repo evaluation with fetcher.analyze()
- [ ] Track skipped repos count
- [ ] Collect savings data

#### Output Display
- [ ] Create savings summary display
- [ ] Show repos analyzed vs. skipped
- [ ] Display API calls saved
- [ ] Display estimated cost saved
- [ ] Display time saved
- [ ] Add --verbose option for skip reasons

---

### Day 5: Testing & Validation (3-4 hours)

#### Unit Tests
- [ ] Create `tests/github/test_smart_fetcher.py`
- [ ] Test Decision enum and StageResult dataclass
- [ ] Test metadata filtering logic
- [ ] Test keyword extraction
- [ ] Test score calculations
- [ ] Mock LLM calls for testing
- [ ] Test stage decision logic
- [ ] Test savings calculations

#### Integration Tests
- [ ] Test full analysis flow (all stages)
- [ ] Test early exit (Stage 1 SKIP)
- [ ] Test fast-tracking (Stage 2 CONTINUE_DEEP)
- [ ] Test thoroughness levels
- [ ] Test with real repo data (cached)
- [ ] Verify savings accuracy

#### Baseline Comparison
- [ ] Run curate with --disable-smart-fetch (baseline)
- [ ] Run curate with smart fetch enabled
- [ ] Compare results (same repos identified?)
- [ ] Measure false negatives (relevant repos skipped)
- [ ] Measure savings (API calls, cost, time)
- [ ] Document comparison results

#### Threshold Tuning
- [ ] Test with different min_quick_score values (0.2, 0.3, 0.4)
- [ ] Test with different high_promise_score values (0.6, 0.7, 0.8)
- [ ] Measure false negative rate for each
- [ ] Measure savings for each
- [ ] Find optimal balance
- [ ] Update default config values

---

### Day 6: Documentation (2-3 hours)

#### User Guide: Smart Fetching
- [ ] Create `docs/user-guide/smart-fetching.md`
- [ ] Explain the concept and benefits
- [ ] Describe the 4-stage pipeline
- [ ] Show examples of cost/time savings
- [ ] Explain when to use each mode
- [ ] Add troubleshooting section

#### Fetch Modes Reference
- [ ] Create `docs/user-guide/fetch-modes.md`
- [ ] Document `fast` mode (minimal analysis)
- [ ] Document `standard` mode (balanced - default)
- [ ] Document `thorough` mode (deep analysis)
- [ ] Document `exhaustive` mode (clone all repos)
- [ ] Create comparison table
- [ ] Add use case recommendations

#### Configuration Documentation
- [ ] Update `docs/user-guide/configuration.md`
- [ ] Add smart_fetch section documentation
- [ ] Explain all configuration options
- [ ] Show example configurations
- [ ] Document threshold tuning

#### README Updates
- [ ] Add Smart Fetching section to main README
- [ ] Show quick example
- [ ] Link to detailed docs
- [ ] Highlight cost/time savings

#### Update Existing Docs
- [ ] Update `docs/USAGE.md` with smart fetch examples
- [ ] Update feature status in `TODO.md`
- [ ] Update `PROJECT_PLAN.md` to mark Phase 2 complete

---

### Day 7: Polish & Finalization (2-3 hours)

#### Code Quality
- [ ] Run black formatter on new code
- [ ] Run ruff linter and fix issues
- [ ] Run mypy type checker and fix issues
- [ ] Add comprehensive docstrings
- [ ] Add type hints to all functions
- [ ] Review code for edge cases

#### Performance Optimization
- [ ] Profile stage execution times
- [ ] Optimize keyword matching
- [ ] Cache keyword extraction
- [ ] Parallelize independent operations
- [ ] Measure performance improvements

#### Error Handling
- [ ] Add try-catch for LLM failures
- [ ] Add fallback for quick LLM check
- [ ] Handle missing README gracefully
- [ ] Add validation for config values
- [ ] Test error scenarios

#### Final Testing
- [ ] Run full test suite
- [ ] Test with different themes
- [ ] Test with different LLM providers
- [ ] Test all fetch modes
- [ ] Test error cases
- [ ] Verify savings calculations

#### Git & PR Prep
- [ ] Review all changes
- [ ] Create comprehensive commit message
- [ ] Push feature branch
- [ ] Create pull request
- [ ] Write PR description with metrics
- [ ] Request review

---

## 📊 Success Criteria

Before marking Phase 2 complete, verify:

- [ ] **Functionality**: All 4 stages working correctly
- [ ] **CLI Integration**: Commands work with all modes
- [ ] **Configuration**: All settings functional
- [ ] **Testing**: >80% code coverage for new code
- [ ] **Documentation**: All user docs complete
- [ ] **Performance**: 3-5x speedup measured
- [ ] **Cost Savings**: 50-70% API reduction measured
- [ ] **Accuracy**: <5% false negative rate
- [ ] **Code Quality**: All linters passing
- [ ] **No Regressions**: Existing tests still pass

---

## 🎯 Metrics to Track

During implementation, measure and document:

1. **API Call Reduction**:
   - Baseline: X calls per curation
   - With smart fetch: Y calls per curation
   - Reduction: (X-Y)/X * 100%

2. **Cost Savings**:
   - Baseline cost: $X per curation
   - Smart fetch cost: $Y per curation
   - Savings: $X-Y ($Z saved, W% reduction)

3. **Time Savings**:
   - Baseline time: X seconds
   - Smart fetch time: Y seconds
   - Speedup: X/Y times faster

4. **Accuracy**:
   - False negatives: N relevant repos skipped
   - False negative rate: N/total relevant repos
   - Target: <5%

5. **Skip Rate**:
   - Repos analyzed: X
   - Repos skipped: Y
   - Skip rate: Y/(X+Y) * 100%
   - Target: 40-60%

---

## 📝 Notes

### Design Decisions
- Use cheap model (Haiku) for quick LLM checks to minimize cost
- Default to standard mode (balanced)
- Enable smart fetch by default (can disable with flag)
- Save traces for later analysis and tuning

### Open Questions
- [ ] Should Stage 4 (code analysis) be implemented in Phase 2 or defer to Phase 3?
  - **Decision**: Implement stub, full implementation in Phase 3
- [ ] What's the optimal min_quick_score threshold?
  - **Decision**: Start with 0.3, tune based on testing
- [ ] Should we cache stage results for repeated curations?
  - **Decision**: Yes, add to Phase 3

### Dependencies
- Existing: LangChain LLM abstraction ✅
- Existing: Prefect pipeline ✅
- Existing: Evaluation system ✅
- New: None required

---

**Last Updated**: 2025-10-10
**Status**: In Progress - Day 1
**Branch**: feature/smart-repo-fetcher
