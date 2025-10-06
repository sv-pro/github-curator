# Declarative Pipeline Implementation Plan

## Overview

This document outlines the phased implementation plan for migrating GitHub Curator to a **Prefect-based declarative pipeline** with caching, parallelization, and incremental computation.

## Goals

- ✅ **Incremental computation** - Only recompute when inputs change
- ✅ **Parallelization** - Run independent tasks concurrently
- ✅ **Caching** - Intelligent result caching with TTL
- ✅ **Resumability** - Recover from failures without restarting
- ✅ **Developer experience** - Simple, Pythonic API
- ✅ **Backward compatibility** - Existing CLI continues to work

## Timeline: 4 Weeks

### Week 1: Foundation & Setup
**Goal:** Install Prefect, basic task conversion

### Week 2: Caching & Parallelization
**Goal:** Enable intelligent caching and parallel execution

### Week 3: Full Migration
**Goal:** Convert all pipeline stages to Prefect tasks

### Week 4: Optimization & Testing
**Goal:** Performance tuning, edge cases, documentation

---

## Phase 1: Foundation & Setup (Week 1)

### Day 1-2: Environment Setup

**Tasks:**
1. **Install Prefect**
   ```bash
   pip install prefect
   pip install prefect-github  # For GitHub integration
   ```

2. **Configure Prefect**
   ```python
   # config/prefect.yaml
   prefect:
     api:
       url: "http://127.0.0.1:4200/api"  # Local server

     results:
       persist_by_default: true
       storage:
         type: "local"
         path: ".prefect-results/"

     tasks:
       default_cache_expiration: 7d
       default_retry_delay: 10s
       max_retries: 3
   ```

3. **Project structure**
   ```
   curator/
   ├── pipeline/
   │   ├── __init__.py
   │   ├── tasks.py           # Prefect task definitions
   │   ├── flows.py           # Prefect flow definitions
   │   ├── config.py          # Prefect configuration
   │   └── cache.py           # Custom cache key functions
   ├── core/                  # Existing modules (unchanged)
   ├── github/
   └── outputs/
   ```

**Deliverables:**
- [ ] Prefect installed and configured
- [ ] Local Prefect server running
- [ ] Basic project structure created
- [ ] Environment validated

### Day 3-5: First Task Conversion

**Tasks:**
1. **Convert IntentStructurer to Prefect task**
   ```python
   # curator/pipeline/tasks.py

   from prefect import task
   from prefect.tasks import task_input_hash
   from datetime import timedelta
   from curator.core.intent_structuring import IntentStructurer

   @task(
       name="structure-intent",
       cache_key_fn=task_input_hash,
       cache_expiration=timedelta(days=7),
       retries=3,
       tags=["intent", "llm"]
   )
   def structure_intent_task(
       theme: str,
       focus_areas: list[str] | None = None,
       exclusions: list[str] | None = None,
       config_path: str = "config/curator.yaml"
   ):
       """Structure natural language theme into formal intent."""
       structurer = IntentStructurer(config_path)
       return structurer.structure_theme(theme, focus_areas, exclusions)
   ```

2. **Create simple test flow**
   ```python
   # curator/pipeline/flows.py

   from prefect import flow

   @flow(name="test-intent-structuring")
   def test_intent_flow(theme: str):
       intent = structure_intent_task(theme)
       return intent
   ```

3. **Test execution**
   ```python
   # examples/test_prefect_basic.py

   from curator.pipeline.flows import test_intent_flow

   if __name__ == "__main__":
       result = test_intent_flow("AI agents with tool use")
       print(f"Intent ID: {result.intent_id}")
       print(f"Dimensions: {len(result.dimensions)}")

       # Run again - should hit cache
       result2 = test_intent_flow("AI agents with tool use")
       print("Second run completed (from cache)")
   ```

**Deliverables:**
- [ ] First Prefect task created and tested
- [ ] Caching verified working
- [ ] Basic flow execution successful
- [ ] Cache invalidation tested

### Day 6-7: Custom Cache Keys

**Tasks:**
1. **Implement content-based cache keys**
   ```python
   # curator/pipeline/cache.py

   import hashlib
   import json
   from typing import Any
   from prefect import TaskRunContext
   from prefect.utilities.hashing import hash_objects

   def intent_cache_key(context: TaskRunContext, parameters: dict) -> str:
       """Custom cache key for intent structuring."""
       cache_data = {
           "theme": parameters["theme"],
           "focus_areas": sorted(parameters.get("focus_areas") or []),
           "exclusions": sorted(parameters.get("exclusions") or []),
           # Include config version to invalidate on config changes
           "config_version": _get_config_version(parameters["config_path"])
       }
       return hash_objects(cache_data)

   def evaluation_cache_key(context: TaskRunContext, parameters: dict) -> str:
       """Custom cache key for evaluations."""
       cache_data = {
           "repo": parameters["context"].full_name,
           "intent_id": parameters["intent"].intent_id,
           "model_version": "claude-sonnet-4-5-20250929",
       }
       return hash_objects(cache_data)
   ```

2. **Update task with custom cache key**
   ```python
   @task(
       cache_key_fn=intent_cache_key,
       cache_expiration=timedelta(days=7)
   )
   def structure_intent_task(...):
       ...
   ```

**Deliverables:**
- [ ] Custom cache key functions implemented
- [ ] Cache keys tested for determinism
- [ ] Documentation for cache strategies

---

## Phase 2: Caching & Parallelization (Week 2)

### Day 8-10: Convert Remaining Core Tasks

**Tasks:**
1. **Validation task**
   ```python
   @task(name="validate-intent", retries=2)
   def validate_intent_task(intent: StructuredIntent):
       validator = Validator()
       return validator.validate_intent(intent)
   ```

2. **Search task** (cached 1 hour)
   ```python
   @task(
       name="search-repos",
       cache_key_fn=search_cache_key,
       cache_expiration=timedelta(hours=1),
       tags=["github"]
   )
   def search_repos_task(intent: StructuredIntent, github_client):
       adaptive_search = AdaptiveSearchStrategy()
       return adaptive_search.adaptive_search(intent.theme, github_client)
   ```

3. **Analysis task** (cached 30 days)
   ```python
   @task(
       name="analyze-repo",
       cache_key_fn=analysis_cache_key,
       cache_expiration=timedelta(days=30),
       retries=3,
       tags=["github", "analysis"]
   )
   def analyze_repo_task(repo: Repository, github_client):
       analyzer = RepositoryAnalyzer(github_client)
       return analyzer.analyze_repository(repo)
   ```

**Deliverables:**
- [ ] All core tasks converted to Prefect
- [ ] Appropriate cache strategies applied
- [ ] Unit tests for each task

### Day 11-12: Implement Parallelization

**Tasks:**
1. **Create parallel evaluation flow**
   ```python
   from prefect import flow
   from prefect.task_runners import ConcurrentTaskRunner

   @flow(
       name="curate-repositories",
       task_runner=ConcurrentTaskRunner()
   )
   def curate_flow(
       theme: str,
       focus_areas: list[str] | None = None,
       min_stars: int = 50
   ):
       # Step 1: Structure intent (cached)
       intent = structure_intent_task(theme, focus_areas)

       # Step 2: Validate intent
       validation = validate_intent_task(intent)

       # Step 3: Search repos (cached 1h)
       repos = search_repos_task(intent)

       # Step 4: Analyze repos in parallel (cached 30d each)
       contexts = analyze_repo_task.map(repos)

       # Step 5: Evaluate in parallel (cached 30d each)
       from prefect import unmapped
       evaluations = evaluate_repo_task.map(
           contexts,
           intent=unmapped(intent)
       )

       # Step 6: Aggregate results
       validation_report = validate_results_task(intent, evaluations)
       reflection = reflect_task(intent, evaluations)

       # Step 7: Generate reports
       return generate_reports_task(
           intent, evaluations, validation_report, reflection
       )
   ```

2. **Configure concurrency limits**
   ```python
   # config/prefect.yaml
   task_runner:
     type: "concurrent"
     max_workers: 10

   tasks:
     analyze_repo:
       max_concurrent: 5  # Respect GitHub rate limits

     evaluate_repo:
       max_concurrent: 3  # LLM API limits
   ```

**Deliverables:**
- [ ] Parallel execution working
- [ ] Concurrency limits configured
- [ ] Performance benchmarks (before/after)

### Day 13-14: Error Handling & Retries

**Tasks:**
1. **Add retry logic with exponential backoff**
   ```python
   from prefect.tasks import exponential_backoff

   @task(
       retries=3,
       retry_delay_seconds=exponential_backoff(backoff_factor=2),
       retry_jitter_factor=0.5
   )
   def evaluate_repo_task(...):
       ...
   ```

2. **Implement failure handling**
   ```python
   @flow
   def curate_flow_with_recovery(theme: str):
       try:
           return curate_flow(theme)
       except Exception as e:
           # Log failure
           logger.error(f"Pipeline failed: {e}")

           # Attempt recovery
           if should_retry(e):
               return curate_flow(theme)
           else:
               raise
   ```

3. **Partial result handling**
   ```python
   @flow
   def robust_curate_flow(theme: str):
       intent = structure_intent_task(theme)
       repos = search_repos_task(intent)

       # Evaluate with failure tolerance
       evaluations = []
       for repo in repos:
           try:
               eval = evaluate_repo_task(repo, intent)
               evaluations.append(eval)
           except Exception as e:
               logger.warning(f"Failed to evaluate {repo.full_name}: {e}")
               continue  # Continue with other repos

       return evaluations
   ```

**Deliverables:**
- [ ] Retry logic implemented
- [ ] Failure recovery tested
- [ ] Partial results handling

---

## Phase 3: Full Migration (Week 3)

### Day 15-17: CLI Integration

**Tasks:**
1. **Update CLI to use Prefect flows**
   ```python
   # curator/__main__.py

   @cli.command()
   @click.argument("theme")
   @click.option("--use-prefect/--no-prefect", default=True)
   def curate(theme: str, use_prefect: bool, **kwargs):
       if use_prefect:
           # Use new Prefect-based pipeline
           from curator.pipeline.flows import curate_flow
           result = curate_flow(
               theme=theme,
               focus_areas=kwargs.get("focus"),
               min_stars=kwargs.get("min_stars")
           )
       else:
           # Use legacy pipeline
           result = legacy_curate(theme, **kwargs)

       # Display results (common code)
       display_results(result)
   ```

2. **Add Prefect CLI commands**
   ```python
   @cli.group()
   def pipeline():
       """Manage Prefect pipeline."""
       pass

   @pipeline.command()
   def status():
       """Show pipeline status and cache stats."""
       # Show cache hit rates, recent runs, etc.

   @pipeline.command()
   def clear_cache():
       """Clear pipeline cache."""
       from prefect import get_client
       # Clear cache logic

   @pipeline.command()
   def dashboard():
       """Open Prefect dashboard."""
       import webbrowser
       webbrowser.open("http://localhost:4200")
   ```

**Deliverables:**
- [ ] CLI integrated with Prefect
- [ ] Legacy mode available as fallback
- [ ] New pipeline commands added

### Day 18-19: Async Support

**Tasks:**
1. **Convert to async tasks**
   ```python
   @task
   async def structure_intent_task_async(theme: str):
       structurer = IntentStructurer()
       # Use async Claude API
       return await structurer.structure_theme_async(theme)

   @task
   async def evaluate_repo_task_async(context, intent):
       evaluator = MetacognitiveEvaluator()
       return await evaluator.evaluate_repository_async(context, intent)
   ```

2. **Async flow**
   ```python
   @flow
   async def curate_flow_async(theme: str):
       intent = await structure_intent_task_async(theme)
       repos = await search_repos_task_async(intent)

       # Parallel async execution
       import asyncio
       contexts = await asyncio.gather(*[
           analyze_repo_task_async(repo) for repo in repos
       ])

       evaluations = await asyncio.gather(*[
           evaluate_repo_task_async(ctx, intent) for ctx in contexts
       ])

       return evaluations
   ```

**Deliverables:**
- [ ] Async tasks implemented
- [ ] Async flow working
- [ ] Performance comparison (sync vs async)

### Day 20-21: Testing & Validation

**Tasks:**
1. **Integration tests**
   ```python
   # tests/test_pipeline_integration.py

   def test_full_pipeline():
       result = curate_flow("test theme")
       assert len(result.evaluations) > 0

   def test_cache_reuse():
       # First run
       result1 = curate_flow("test theme")
       time1 = result1.execution_time

       # Second run (should be faster)
       result2 = curate_flow("test theme")
       time2 = result2.execution_time

       assert time2 < time1 * 0.3  # At least 70% faster

   def test_incremental_computation():
       # Run with min_stars=50
       result1 = curate_flow("theme", min_stars=50)

       # Run with min_stars=100 (should reuse most cached results)
       result2 = curate_flow("theme", min_stars=100)

       # Verify cache hits
       assert cache_hit_rate() > 0.8
   ```

2. **Performance benchmarks**
   ```python
   # benchmarks/pipeline_performance.py

   def benchmark_parallel_vs_sequential():
       # Measure time for sequential
       start = time.time()
       sequential_result = curate_flow_sequential("theme")
       seq_time = time.time() - start

       # Measure time for parallel
       start = time.time()
       parallel_result = curate_flow("theme")
       par_time = time.time() - start

       speedup = seq_time / par_time
       print(f"Speedup: {speedup}x")
   ```

**Deliverables:**
- [ ] Comprehensive test suite
- [ ] Performance benchmarks
- [ ] Edge cases covered

---

## Phase 4: Optimization & Polish (Week 4)

### Day 22-24: Advanced Caching

**Tasks:**
1. **Implement cache warming**
   ```python
   @flow
   def warm_cache_flow(themes: list[str]):
       """Pre-populate cache for common queries."""
       for theme in themes:
           structure_intent_task(theme)
   ```

2. **Cache analytics**
   ```python
   @flow
   def cache_analytics():
       """Analyze cache performance."""
       from prefect import get_client

       stats = {
           "hit_rate": calculate_hit_rate(),
           "size": get_cache_size(),
           "top_cached_tasks": get_top_cached(),
           "eviction_rate": get_eviction_rate()
       }
       return stats
   ```

3. **Smart cache invalidation**
   ```python
   def invalidate_if_stale(cache_key: str, max_age: timedelta):
       """Invalidate cache entries older than max_age."""
       entry = get_cache_entry(cache_key)
       if entry and (datetime.now() - entry.created) > max_age:
           delete_cache_entry(cache_key)
   ```

**Deliverables:**
- [ ] Cache warming implemented
- [ ] Cache analytics dashboard
- [ ] Smart invalidation logic

### Day 25-26: Documentation

**Tasks:**
1. **User guide**
   ```markdown
   # Prefect Pipeline User Guide

   ## Quick Start

   ## Caching Behavior

   ## Performance Tuning

   ## Troubleshooting
   ```

2. **Developer guide**
   ```markdown
   # Adding New Pipeline Tasks

   ## Task Design Principles

   ## Cache Key Design

   ## Testing Tasks
   ```

3. **Migration guide**
   ```markdown
   # Migrating from Legacy Pipeline

   ## What's Changed

   ## Step-by-Step Migration

   ## Common Issues
   ```

**Deliverables:**
- [ ] User documentation complete
- [ ] Developer documentation
- [ ] Migration guide
- [ ] API reference

### Day 27-28: Production Readiness

**Tasks:**
1. **Monitoring & observability**
   ```python
   from prefect import get_run_logger

   @task
   def monitored_task(...):
       logger = get_run_logger()
       logger.info("Task started", extra={"repo": repo.name})

       try:
           result = execute()
           logger.info("Task completed", extra={"duration": duration})
           return result
       except Exception as e:
           logger.error("Task failed", extra={"error": str(e)})
           raise
   ```

2. **Production configuration**
   ```yaml
   # config/prefect-prod.yaml
   prefect:
     api:
       url: "${PREFECT_API_URL}"  # Prefect Cloud

     results:
       persist_by_default: true
       storage:
         type: "s3"
         bucket: "curator-cache"

     tasks:
       default_cache_expiration: 30d
       max_retries: 5
   ```

3. **Deployment scripts**
   ```python
   # scripts/deploy_pipeline.py

   from prefect.deployments import Deployment
   from curator.pipeline.flows import curate_flow

   deployment = Deployment.build_from_flow(
       flow=curate_flow,
       name="curator-production",
       work_queue_name="curator",
       parameters={"theme": "AI agents"},
       schedule="0 0 * * *"  # Daily at midnight
   )

   deployment.apply()
   ```

**Deliverables:**
- [ ] Monitoring configured
- [ ] Production settings
- [ ] Deployment automation
- [ ] Health checks

---

## Success Criteria

### Performance Metrics
- [ ] **Cache hit rate**: >80% on repeated similar queries
- [ ] **Speedup (parallel)**: 3-5x vs sequential
- [ ] **Speedup (incremental)**: 5-10x when changing only constraints
- [ ] **Memory usage**: <500MB for 50 repo evaluations

### Reliability
- [ ] **Resumability**: 100% of failures can resume
- [ ] **Cache consistency**: No corruption or stale data
- [ ] **Error handling**: Graceful degradation on partial failures

### Developer Experience
- [ ] **Migration**: <1 day for new task addition
- [ ] **Debugging**: Clear error messages and logs
- [ ] **Testing**: <5min full test suite execution

### User Experience
- [ ] **CLI**: Backward compatible, no breaking changes
- [ ] **Performance**: Visible speedup on repeated queries
- [ ] **Reliability**: Fewer timeout/failure errors

---

## Rollout Plan

### Week 1: Internal Testing
- Enable Prefect pipeline with `--use-prefect` flag
- Test with development team
- Collect feedback

### Week 2: Beta Release
- Make Prefect default, keep legacy as `--use-legacy`
- Public beta announcement
- Monitor metrics

### Week 3: Stabilization
- Fix reported issues
- Performance tuning
- Documentation updates

### Week 4: Full Release
- Remove legacy pipeline
- Announce v2.0
- Celebration! 🎉

---

## Risk Mitigation

### Risk: Prefect adds too much overhead
**Mitigation:** Keep legacy pipeline as fallback, benchmark continuously

### Risk: Cache corruption
**Mitigation:** Implement checksum validation, cache versioning

### Risk: Breaking changes in Prefect
**Mitigation:** Pin Prefect version, test upgrades in staging

### Risk: Team unfamiliar with Prefect
**Mitigation:** Training sessions, comprehensive docs, pair programming

---

## Next Steps

1. **Review this plan** with team
2. **Set up development environment** (Day 1)
3. **Begin Phase 1** implementation
4. **Daily standups** to track progress
5. **Weekly demos** to stakeholders

## Questions for Discussion

1. Should we start with async from day 1, or migrate later?
2. Local Prefect server vs. Prefect Cloud?
3. Cache storage: local filesystem or S3/GCS?
4. Monitoring: Prefect UI only, or additional APM?
5. Testing strategy: Integration tests or E2E focus?
