# Declarative Build-System Pipeline Design

## Executive Summary

This design document proposes a **declarative, build-system-alike, caching-based** architecture for handling intents in the GitHub Curator. The new system transforms the imperative pipeline into a dependency-driven, incremental computation framework inspired by build systems like Make, Bazel, and Shake.

**Recommendation: Use Prefect** as the foundation framework for its excellent task caching, lightweight Python-first design, and minimal setup overhead while providing production-ready orchestration capabilities.

## Current Architecture Analysis

### Current Flow (Imperative)
```
User Input → Structure Intent → Validate → Search → Analyze → Evaluate → Validate → Reflect → Report
```

**Issues with current approach:**
1. **No incremental computation** - re-runs entire pipeline even if only theme changes slightly
2. **Implicit dependencies** - components coupled through direct function calls
3. **Limited caching** - only intent structuring has basic caching
4. **No parallelization** - sequential execution of independent tasks
5. **Hard to resume** - if pipeline fails, must restart from beginning
6. **No dependency tracking** - can't determine what needs to be recomputed

### Current Caching
- **Intent structuring**: Basic SHA256 hash-based caching (theme + focus + exclusions)
- **Other modules**: No caching
- **Cache invalidation**: None (cache never expires or validates freshness)

## Proposed Architecture: Declarative Build Pipeline

### Core Principles

1. **Declarative Task Definitions** - Tasks declare inputs, outputs, and dependencies
2. **Content-Addressable Storage** - Results stored by hash of inputs (like Nix, Bazel)
3. **Automatic Dependency Resolution** - Build system determines execution order
4. **Incremental Computation** - Only recompute when inputs change
5. **Parallel Execution** - Independent tasks run concurrently
6. **Resumable Pipelines** - Failed pipelines can resume from last successful step

### Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Pipeline Definition                      │
│  (Declarative YAML/Python describing tasks & dependencies)   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Dependency Graph Builder                   │
│         (Constructs DAG from task definitions)               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Cache/Store Manager                       │
│   (Content-addressable store with hash-based retrieval)      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     Task Executor                            │
│  (Executes tasks, handles parallelism, caching, retries)     │
└─────────────────────────────────────────────────────────────┘
```

### Task Model

Each task is a pure function with:

```python
@task
class StructureIntentTask:
    """Task definition with declarative dependencies."""

    # Inputs (dependencies)
    theme: str
    focus_areas: Optional[List[str]]
    exclusions: Optional[List[str]]
    config: Config

    # Output type
    output_type: Type = StructuredIntent

    # Cache key computation
    def compute_cache_key(self) -> str:
        return hash_inputs(
            self.theme,
            self.focus_areas,
            self.exclusions,
            self.config.version  # Config changes invalidate cache
        )

    # Execution logic
    async def execute(self, ctx: ExecutionContext) -> StructuredIntent:
        # Check cache first
        if cached := ctx.cache.get(self.compute_cache_key()):
            return cached

        # Execute task logic
        result = await self._generate_intent()

        # Store in cache
        ctx.cache.put(self.compute_cache_key(), result)
        return result
```

### Dependency Graph

Tasks declare dependencies implicitly through inputs:

```python
# Task definitions
structure_intent = StructureIntentTask(
    theme=user_input.theme,
    focus_areas=user_input.focus,
    exclusions=user_input.exclude,
    config=config
)

validate_intent = ValidateIntentTask(
    intent=structure_intent.output  # Dependency!
)

search_repos = SearchRepositoriesTask(
    intent=structure_intent.output,
    github_client=github_client
)

# Parallel evaluation tasks (one per repo)
evaluate_tasks = [
    EvaluateRepoTask(
        repo=repo,
        intent=structure_intent.output,
        context=AnalyzeRepoTask(repo=repo).output
    )
    for repo in search_repos.output
]

# Aggregation
validate_results = ValidateResultsTask(
    intent=structure_intent.output,
    evaluations=[t.output for t in evaluate_tasks]
)
```

The build system automatically:
1. Builds dependency DAG
2. Determines execution order (topological sort)
3. Identifies parallelizable tasks
4. Checks cache for each task
5. Executes only necessary tasks

### Content-Addressable Caching

#### Hash Function
```python
def compute_cache_key(task: Task) -> str:
    """Compute deterministic hash of task inputs."""
    input_data = {
        'task_type': task.__class__.__name__,
        'task_version': task.VERSION,  # For schema changes
        'inputs': serialize_inputs(task.inputs),
        'config': task.config.to_hash_dict()
    }
    return hashlib.sha256(
        json.dumps(input_data, sort_keys=True).encode()
    ).hexdigest()
```

#### Cache Storage Structure
```
.curator-cache/
├── intents/
│   ├── a3f2e1b9.../  # Hash-based directory
│   │   ├── meta.json      # Metadata (created_at, inputs hash)
│   │   └── result.json    # Cached result
│   └── d7c8b4a2.../
├── evaluations/
│   ├── repo-a/
│   │   └── 9e4f2a1c.../
│   └── repo-b/
└── validations/
    └── 1a2b3c4d.../
```

#### Cache Validation
```python
class CacheEntry:
    key: str
    created_at: datetime
    inputs_hash: str
    result: Any

    def is_valid(self, max_age: Optional[timedelta] = None) -> bool:
        """Check if cache entry is still valid."""
        if max_age and datetime.now() - self.created_at > max_age:
            return False
        return True
```

### Pipeline Definition (Declarative YAML)

```yaml
# .curator/pipeline.yaml
version: 1.0

tasks:
  structure_intent:
    type: StructureIntentTask
    inputs:
      theme: ${user.theme}
      focus_areas: ${user.focus}
      exclusions: ${user.exclude}
      config: ${config}
    cache:
      enabled: true
      max_age: 7d  # Cache valid for 7 days

  validate_intent:
    type: ValidateIntentTask
    inputs:
      intent: ${tasks.structure_intent.output}
    depends_on:
      - structure_intent
    cache:
      enabled: true
      key_includes:
        - intent.dimensions
        - validation.rules

  search_repos:
    type: SearchRepositoriesTask
    inputs:
      intent: ${tasks.structure_intent.output}
      github_client: ${github_client}
    depends_on:
      - structure_intent
    cache:
      enabled: true
      max_age: 1h  # GitHub results change frequently

  analyze_repos:
    type: ParallelMapTask
    task: AnalyzeRepoTask
    inputs:
      repos: ${tasks.search_repos.output}
    parallel: true
    max_workers: 10
    cache:
      enabled: true
      per_item: true  # Cache each repo analysis separately

  evaluate_repos:
    type: ParallelMapTask
    task: EvaluateRepoTask
    inputs:
      contexts: ${tasks.analyze_repos.output}
      intent: ${tasks.structure_intent.output}
    depends_on:
      - structure_intent
      - analyze_repos
    parallel: true
    max_workers: 5
    cache:
      enabled: true
      per_item: true

  validate_results:
    type: ValidateResultsTask
    inputs:
      intent: ${tasks.structure_intent.output}
      evaluations: ${tasks.evaluate_repos.output}
    depends_on:
      - structure_intent
      - evaluate_repos

  reflect:
    type: ReflectionTask
    inputs:
      evaluations: ${tasks.evaluate_repos.output}
      intent: ${tasks.structure_intent.output}
    depends_on:
      - evaluate_repos
      - structure_intent
    cache:
      enabled: true

  generate_reports:
    type: GenerateReportsTask
    inputs:
      intent: ${tasks.structure_intent.output}
      evaluations: ${tasks.evaluate_repos.output}
      validation: ${tasks.validate_results.output}
      reflection: ${tasks.reflect.output}
    depends_on:
      - structure_intent
      - evaluate_repos
      - validate_results
      - reflect
    cache:
      enabled: false  # Always regenerate reports
```

### Python API (Alternative to YAML)

```python
from curator.pipeline import Pipeline, Task, task

@task
async def structure_intent(theme: str, config: Config) -> StructuredIntent:
    """Structure natural language theme into formal intent."""
    # Implementation
    ...

@task
async def evaluate_repo(
    context: RepositoryContext,
    intent: StructuredIntent
) -> EvaluationReport:
    """Evaluate single repository."""
    ...

# Build pipeline programmatically
pipeline = Pipeline()

# Add tasks with dependencies
intent = pipeline.add(structure_intent(
    theme=user_input.theme,
    config=config
))

repos = pipeline.add(search_repos(intent=intent))

# Map operation (parallel)
evaluations = pipeline.map(
    evaluate_repo,
    contexts=repos,
    intent=intent,
    parallel=True,
    max_workers=10
)

reflection = pipeline.add(reflect(
    evaluations=evaluations,
    intent=intent
))

# Execute pipeline
results = await pipeline.execute()
```

## Implementation Strategy

### Phase 1: Core Framework (Week 1)
**Goal:** Build foundation for declarative task execution

1. **Task abstraction**
   - Base `Task` class with inputs/outputs
   - `@task` decorator for function-based tasks
   - Task metadata (version, cache policy)

2. **Dependency graph**
   - DAG builder from task definitions
   - Topological sort for execution order
   - Cycle detection

3. **Cache manager**
   - Content-addressable storage
   - Hash-based key generation
   - Cache validation (age, invalidation rules)

4. **Basic executor**
   - Sequential execution
   - Cache lookup/store
   - Error handling

**Deliverables:**
- `curator/pipeline/task.py`
- `curator/pipeline/graph.py`
- `curator/pipeline/cache.py`
- `curator/pipeline/executor.py`
- Basic tests

### Phase 2: Parallel Execution (Week 2)
**Goal:** Enable concurrent task execution

1. **Async executor**
   - Asyncio-based parallel execution
   - Worker pool management
   - Task batching

2. **Parallel operators**
   - `map()` for parallel iterations
   - `gather()` for independent tasks
   - Progress tracking

3. **Error recovery**
   - Retry logic
   - Partial failure handling
   - Resume from checkpoint

**Deliverables:**
- `curator/pipeline/parallel.py`
- `curator/pipeline/retry.py`
- Performance benchmarks

### Phase 3: Migrate Existing Components (Week 3)
**Goal:** Convert current pipeline to declarative tasks

1. **Convert modules to tasks**
   - `IntentStructuringTask` (refactor existing)
   - `SearchRepositoriesTask`
   - `AnalyzeRepositoryTask`
   - `EvaluateRepositoryTask`
   - `ValidationTask`
   - `ReflectionTask`
   - `ReportGenerationTask`

2. **Pipeline definition**
   - YAML pipeline specification
   - Python API for programmatic access
   - CLI integration

3. **Migration path**
   - Keep old API as facade
   - Gradual migration
   - Backwards compatibility

**Deliverables:**
- Converted task modules
- Pipeline definitions
- Migration guide

### Phase 4: Advanced Features (Week 4)
**Goal:** Add sophisticated caching and optimization

1. **Smart cache invalidation**
   - Dependency-based invalidation
   - Partial cache updates
   - Cache garbage collection

2. **Optimization**
   - Task fusion (combine small tasks)
   - Predictive caching
   - Resource-aware scheduling

3. **Observability**
   - Execution traces
   - Cache hit/miss metrics
   - Performance profiling

**Deliverables:**
- Advanced caching features
- Monitoring dashboard
- Performance documentation

## Benefits

### 1. Incremental Computation
**Before:**
```bash
$ curator curate "AI agents" --min-stars 100
# Takes 5 minutes

$ curator curate "AI agents" --min-stars 50  # Different star count
# Takes 5 minutes again (re-does everything!)
```

**After:**
```bash
$ curator curate "AI agents" --min-stars 100
# Takes 5 minutes, caches: intent, analysis, evaluations

$ curator curate "AI agents" --min-stars 50
# Takes 30 seconds (only re-runs search, reuses cached evaluations)
```

### 2. Parallelization
**Before:** Sequential evaluation
```
Repo 1 → Repo 2 → Repo 3 → ... → Repo 20  (5 min)
```

**After:** Parallel evaluation
```
Repo 1 ┐
Repo 2 ├→ (concurrent) → Results  (1 min)
Repo 3 ┘
```

### 3. Resumability
**Before:**
```bash
# Pipeline fails at evaluation step 15/20
# Must restart from beginning, lose 14 evaluations
```

**After:**
```bash
# Pipeline fails at evaluation step 15/20
# Resumes from step 15, reuses cached results 1-14
```

### 4. Experimentation
```bash
# Try different dimension weights without re-analyzing repos
$ curator curate "theme" --weights architectural:0.5,docs:0.5
$ curator curate "theme" --weights architectural:0.3,docs:0.7
# Only re-runs final scoring, not analysis!
```

## Migration Path

### Phase 1: Parallel Systems
- Keep existing imperative pipeline
- Implement new declarative pipeline alongside
- Add `--use-declarative-pipeline` flag

### Phase 2: Feature Parity
- Ensure all features work in new system
- Add migration tests
- Document differences

### Phase 3: Gradual Transition
- Make declarative pipeline default
- Keep legacy as `--use-legacy-pipeline`
- Deprecation warnings

### Phase 4: Complete Migration
- Remove legacy code
- Clean up abstractions
- Full documentation

## Example Usage Scenarios

### Scenario 1: Iterative Refinement
```bash
# Initial run
$ curator curate "ML visualization tools"
# Caches: intent, search, analysis, evaluations

# Refine theme (only re-structures intent, reuses rest)
$ curator curate "ML visualization tools for time series"
# Reuses: search results, analysis, evaluations

# Adjust star threshold (only re-runs search)
$ curator curate "ML visualization tools" --min-stars 500
# Reuses: intent, analysis (filters cached repos), evaluations
```

### Scenario 2: Partial Pipeline Execution
```python
# Only run specific stages
pipeline = Pipeline.from_yaml('.curator/pipeline.yaml')

# Just get structured intent
intent = await pipeline.execute_until('structure_intent')

# Run up to search
repos = await pipeline.execute_until('search_repos')

# Full execution
results = await pipeline.execute()
```

### Scenario 3: Custom Pipeline
```python
# Extend with custom tasks
@task
async def filter_by_language(
    repos: List[Repository],
    language: str
) -> List[Repository]:
    return [r for r in repos if r.language == language]

pipeline = Pipeline()
intent = pipeline.add(structure_intent(...))
all_repos = pipeline.add(search_repos(intent=intent))
python_repos = pipeline.add(filter_by_language(
    repos=all_repos,
    language='Python'
))
evaluations = pipeline.map(evaluate_repo, repos=python_repos, ...)

await pipeline.execute()
```

## Framework Evaluation

After researching existing Python pipeline frameworks, here's the evaluation:

### Considered Frameworks

| Framework | Pros | Cons | Fit Score |
|-----------|------|------|-----------|
| **Prefect** | ✅ Built-in task caching<br>✅ Lightweight, Python-first<br>✅ Minimal setup<br>✅ Dynamic workflows<br>✅ Great DX | ❌ No native data lineage<br>❌ Less opinionated | **9/10** |
| **Dagster** | ✅ Asset-based model<br>✅ Native lineage<br>✅ Modular architecture<br>✅ Great for data pipelines | ❌ More complex setup<br>❌ No built-in task caching<br>❌ Heavier weight | **7/10** |
| **Dask** | ✅ Excellent parallelization<br>✅ Opportunistic caching<br>✅ Familiar API | ❌ Optimized for compute, not workflows<br>❌ No persistent caching<br>❌ Limited workflow features | **6/10** |
| **Snakemake** | ✅ Build-system approach<br>✅ Content-based caching<br>✅ Scientific workflow focus | ❌ YAML-heavy, less Pythonic<br>❌ File-based paradigm<br>❌ Steeper learning curve | **7/10** |
| **Apache Airflow** | ✅ Mature ecosystem<br>✅ Strong community<br>✅ Production-proven | ❌ Heavy infrastructure<br>❌ Complex setup<br>❌ Task-centric not data-centric | **5/10** |
| **Luigi** | ✅ Simple design<br>✅ File targets | ❌ Less active development<br>❌ Limited features<br>❌ No modern async support | **4/10** |
| **Custom (from scratch)** | ✅ Perfect fit for needs<br>✅ No dependencies<br>✅ Full control | ❌ Development time<br>❌ Maintenance burden<br>❌ Missing features | **6/10** |

### Recommendation: **Prefect**

**Why Prefect wins:**

1. **Native Task Caching** - Built-in, production-ready caching based on inputs
   ```python
   @task(cache_key_fn=task_input_hash, cache_expiration=timedelta(days=7))
   async def structure_intent(theme: str) -> StructuredIntent:
       # Automatically cached based on inputs
       ...
   ```

2. **Lightweight & Pythonic** - Minimal boilerplate, pure Python
   ```python
   @flow
   async def curate_repos(theme: str):
       intent = await structure_intent(theme)
       repos = await search_repos(intent)
       evaluations = await evaluate_repos.map(repos, intent=intent)
       return await generate_report(intent, evaluations)
   ```

3. **Dynamic Workflows** - Unlike Airflow's static DAGs, Prefect supports runtime decisions
   ```python
   if intent.requires_deep_analysis:
       results = await deep_eval(repos)
   else:
       results = await quick_eval(repos)
   ```

4. **Incremental Adoption** - Can wrap existing code with minimal changes
   ```python
   @task
   async def existing_function(arg):
       # Your current code unchanged
       return result
   ```

5. **Production Features Out-of-Box**
   - Automatic retries with exponential backoff
   - Failure handling and notifications
   - Observability dashboard
   - Distributed execution
   - Concurrent task execution

### Prefect Integration Architecture

```python
# curator/pipeline/prefect_tasks.py

from prefect import task, flow
from prefect.tasks import task_input_hash
from datetime import timedelta

@task(
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(days=7),
    retries=3
)
async def structure_intent_task(
    theme: str,
    focus_areas: List[str],
    config: Config
) -> StructuredIntent:
    """Cache intent for 7 days based on inputs."""
    structurer = IntentStructurer(config)
    return await structurer.structure_theme(theme, focus_areas)

@task(
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(hours=1)
)
async def search_repos_task(
    intent: StructuredIntent,
    github_client: GitHubAPIClient
) -> List[Repository]:
    """Cache GitHub search for 1 hour."""
    return await github_client.search(intent)

@task(
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(days=30),
    persist_result=True
)
async def analyze_repo_task(
    repo: Repository,
    github_client: GitHubAPIClient
) -> RepositoryContext:
    """Cache repo analysis for 30 days (repos rarely change structure)."""
    analyzer = RepositoryAnalyzer(github_client)
    return await analyzer.analyze_repository(repo)

@task(
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(days=30)
)
async def evaluate_repo_task(
    context: RepositoryContext,
    intent: StructuredIntent
) -> EvaluationReport:
    """Cache evaluations for 30 days."""
    evaluator = MetacognitiveEvaluator()
    return await evaluator.evaluate_repository(context, intent)

@flow(name="curate-repositories")
async def curate_repositories_flow(
    theme: str,
    focus_areas: List[str] = None,
    min_stars: int = 50
) -> CurationResult:
    """Main curation flow with automatic caching and parallelization."""

    # Step 1: Structure intent (cached)
    intent = await structure_intent_task(theme, focus_areas or [])

    # Step 2: Search repos (cached for 1 hour)
    repos = await search_repos_task(intent)

    # Step 3: Analyze repos in parallel (each cached 30 days)
    contexts = await analyze_repo_task.map(repos)

    # Step 4: Evaluate in parallel (each cached 30 days)
    evaluations = await evaluate_repo_task.map(
        contexts,
        intent=unmapped(intent)  # Same intent for all
    )

    # Step 5: Validate and reflect (not cached, always fresh)
    validation = await validate_results_task(intent, evaluations)
    reflection = await reflect_task(intent, evaluations)

    # Step 6: Generate reports
    return await generate_reports_task(
        intent, evaluations, validation, reflection
    )
```

### Migration Strategy with Prefect

**Phase 1: Wrap Existing (Week 1)**
```python
# Minimal change - just add @task decorators
from prefect import task

@task
def structure_intent(theme: str):
    # Existing code unchanged
    return IntentStructurer().structure_theme(theme)
```

**Phase 2: Add Caching (Week 2)**
```python
@task(cache_key_fn=task_input_hash, cache_expiration=timedelta(days=7))
def structure_intent(theme: str):
    # Same code, now cached
    return IntentStructurer().structure_theme(theme)
```

**Phase 3: Parallelize (Week 3)**
```python
@flow
async def curate(theme: str):
    intent = await structure_intent(theme)
    repos = await search_repos(intent)
    # Parallel evaluation - just use .map()
    evaluations = await evaluate_repo.map(repos, intent=unmapped(intent))
    return evaluations
```

**Phase 4: Optimize (Week 4)**
- Fine-tune cache expiration
- Add conditional logic
- Implement custom cache keys
- Set up Prefect Cloud (optional)

### Why Not Build Custom?

While a custom solution would give perfect control, Prefect provides:

- **Immediate value**: Caching works day 1
- **Production-ready**: Retries, monitoring, error handling built-in
- **Active development**: Regular updates, bug fixes, features
- **Community**: Existing patterns, examples, support
- **Lower TCO**: Less code to maintain

**Time saved:** 3-4 weeks of development, ongoing maintenance

### Alternative: Hybrid Approach

If Prefect feels too heavy, consider:

```python
# Use Prefect just for caching + orchestration
# Keep custom logic for domain-specific features

from prefect import task, flow
from curator.pipeline.custom import IncrementalCache

@task(cache_key_fn=custom_hash_fn)
async def cached_task(inputs):
    # Prefect handles caching
    return await execute_logic(inputs)
```

## Technical Considerations

### Cache Size Management
- **TTL-based expiration**: Different TTLs per task type
- **LRU eviction**: Remove least recently used when space limited
- **Garbage collection**: Periodic cleanup of orphaned entries

### Determinism
- **Ensure reproducibility**: Same inputs → same outputs
- **Version tasks**: Schema changes invalidate cache
- **Seal external deps**: Pin API versions, model versions

### Monitoring
- **Metrics to track:**
  - Cache hit/miss ratio per task type
  - Task execution time distribution
  - Dependency graph depth/width
  - Memory usage per task

## Success Metrics

1. **Performance:**
   - 80% cache hit rate on repeated similar queries
   - 5x speedup on incremental runs
   - 3x speedup with parallelization

2. **Usability:**
   - Intuitive pipeline definition
   - Easy to add custom tasks
   - Clear error messages

3. **Reliability:**
   - Resumable pipelines (100% of failures)
   - Consistent cache behavior
   - No cache corruption

## Conclusion

This declarative, build-system-inspired architecture transforms the GitHub Curator from an imperative script into a sophisticated, incremental computation engine. The benefits include:

- ✅ **Faster iterations** through intelligent caching
- ✅ **Better resource utilization** via parallelization
- ✅ **Improved reliability** with resumable pipelines
- ✅ **Enhanced extensibility** through composable tasks
- ✅ **Superior developer experience** with declarative definitions

The phased implementation ensures gradual migration with minimal disruption while delivering immediate value through incremental improvements.
