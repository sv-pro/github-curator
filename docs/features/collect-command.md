# Feature: Collect Command Restoration

## Overview

The `collect` command builds and maintains the knowledge base by collecting repositories from GitHub topics or directly specified repos. It supports incremental updates and refresh modes to keep the knowledge base current.

## Status

**Currently**: ⚠️ MISSING (was removed)
**Last seen**: Commit `1c91c32` (docs: Update documentation for new mark and collect commands)
**Priority**: P1 (High - essential for knowledge base building)

## Original Implementation

### Command Signature
```bash
curator collect [OPTIONS] [TOPIC]
```

### Options
- `[TOPIC]` - GitHub topic to search for (e.g., "machine-learning")
- `--repo <owner/repo>` - Add specific repository (can be used multiple times)
- `--limit <int>` - Maximum repositories to collect (default: 100)
- `--min-stars <int>` - Minimum star count filter (default: 100)
- `--language <str>` - Filter by programming language
- `--knowledge-base <path>` - Knowledge base directory (default: .curator/knowledge)
- `--refresh` - Update existing repositories with latest data
- `--use-git-clone` - Clone repos locally for deeper analysis
- `--config <path>` - Config file path

### Example Usage
```bash
# Collect repositories by topic
curator collect machine-learning --limit 50 --min-stars 500

# Add specific repositories
curator collect --repo fastapi/fastapi --repo tiangolo/typer

# Refresh existing knowledge base
curator collect machine-learning --refresh

# Filter by language
curator collect web-framework --language python --limit 100

# Use git clone for deeper analysis
curator collect async --use-git-clone --limit 20
```

### Knowledge Base Structure
```
.curator/knowledge/
├── metadata.json                # Stats: total repos, topics, last updated
├── repositories.jsonl           # One repo per line (streaming format)
├── topic_patterns.json          # Topic → features/keywords/examples
└── topics/
    ├── machine-learning.json    # Repos tagged with this topic
    ├── web-framework.json
    └── async.json
```

### Repository Entry Format
```json
{
  "full_name": "fastapi/fastapi",
  "name": "fastapi",
  "owner": "fastapi",
  "description": "FastAPI framework, high performance, easy to learn...",
  "url": "https://github.com/fastapi/fastapi",
  "stars": 65000,
  "language": "Python",
  "topics": ["python", "fastapi", "async", "web-framework", "api"],
  "created_at": "2018-12-08T08:21:47Z",
  "updated_at": "2025-10-06T10:30:00Z",
  "collected_at": "2025-10-06T12:00:00Z",
  "features": {
    "async_support": true,
    "type_hints": true,
    "documentation": "extensive",
    "test_coverage": 0.95
  }
}
```

## Restoration Plan

### Step 1: Extract Original Code (30 min)
```bash
# Extract collect command from git history
git show 1c91c32:curator/__main__.py | grep -A 100 "def collect"

# Extract knowledge base management code
git show 1c91c32:curator/knowledge/ --name-only
```

### Step 2: Update for Current Architecture (2 hours)

**Changes needed**:
1. Use Prefect tasks for collection workflow
2. Integrate with hybrid storage (ChromaDB + NetworkX)
3. Use LangChain for embeddings generation
4. Update error handling (Anthropic vs GitHub detection)

**New implementation**:
```python
# curator/__main__.py

@cli.command()
@click.argument("topic", required=False)
@click.option("--repo", multiple=True, help="Specific repository to add (owner/repo)")
@click.option("--limit", default=100, help="Maximum repositories to collect")
@click.option("--min-stars", default=100, help="Minimum star count")
@click.option("--language", help="Filter by programming language")
@click.option("--knowledge-base", default=".curator/knowledge", help="Knowledge base path")
@click.option("--refresh", is_flag=True, help="Update existing repositories")
@click.option("--use-git-clone", is_flag=True, help="Clone repos for deeper analysis")
@click.option("--config", default="config/curator.yaml", help="Config file path")
def collect(topic, repo, limit, min_stars, language, knowledge_base, refresh, use_git_clone, config):
    """Collect repositories and add to knowledge base.

    TOPIC: GitHub topic to search for (e.g., "machine-learning")

    Use --repo to add specific repositories instead of searching by topic.
    By default, skips repositories already in the knowledge base.
    Use --refresh to update existing repos with latest data.
    """
    from curator.commands.collect import collect_repositories

    try:
        # Validate inputs
        if not topic and not repo:
            click.echo("❌ Error: Provide either TOPIC or --repo", err=True)
            raise click.Abort()

        # Collect repositories
        result = collect_repositories(
            topic=topic,
            specific_repos=list(repo) if repo else None,
            limit=limit,
            min_stars=min_stars,
            language=language,
            knowledge_base_path=knowledge_base,
            refresh_existing=refresh,
            use_git_clone=use_git_clone,
            config_path=config
        )

        # Display results
        click.echo(f"\n✅ Collection complete:")
        click.echo(f"  - Repositories collected: {result['collected_count']}")
        click.echo(f"  - Repositories updated: {result['updated_count']}")
        click.echo(f"  - Repositories skipped: {result['skipped_count']}")
        click.echo(f"  - New topics discovered: {result['new_topics_count']}")
        click.echo(f"  - Knowledge base: {knowledge_base}")

        if result.get('errors'):
            click.echo(f"\n⚠️  Warnings: {len(result['errors'])} repositories failed", err=True)

    except Exception as e:
        error_msg = str(e)
        if "github" in error_msg.lower() or "rate limit" in error_msg.lower():
            click.echo("\n❌ GitHub API Error:", err=True)
            click.echo("  - Check GITHUB_TOKEN is valid and has sufficient rate limit", err=True)
            click.echo("  - GitHub rate limit: 5000 req/hour (authenticated)", err=True)
        else:
            click.echo(f"\n❌ Error collecting repositories: {e}", err=True)
        raise click.Abort()
```

### Step 3: Create Prefect Tasks (2 hours)
```python
# curator/pipeline/tasks.py

@task(
    name="search-github-repos",
    cache_key_fn=search_cache_key,
    cache_expiration=timedelta(hours=6),  # Shorter TTL for GitHub data
    retries=3,
    retry_delay_seconds=exponential_backoff(backoff_factor=2),
    tags=["github", "search", "collection"]
)
def search_github_repos_task(
    topic: str,
    limit: int = 100,
    min_stars: int = 100,
    language: Optional[str] = None
) -> list[dict]:
    """Search GitHub for repositories matching criteria."""
    from curator.github.api_client import GitHubClient

    client = GitHubClient()
    return client.search_repositories(
        topic=topic,
        limit=limit,
        min_stars=min_stars,
        language=language
    )


@task(
    name="analyze-repository",
    cache_key_fn=repo_cache_key,
    cache_expiration=timedelta(days=1),
    retries=3,
    tags=["github", "analysis", "collection"]
)
def analyze_repository_task(
    repo_name: str,
    use_git_clone: bool = False
) -> dict:
    """Analyze repository and extract features."""
    from curator.github.repo_analyzer import RepoAnalyzer

    analyzer = RepoAnalyzer(use_git_clone=use_git_clone)
    return analyzer.analyze(repo_name)


@task(
    name="generate-embeddings",
    cache_key_fn=embedding_cache_key,
    cache_expiration=timedelta(days=30),  # Embeddings rarely change
    retries=2,
    tags=["embeddings", "llm", "collection"]
)
def generate_embeddings_task(repo_data: dict) -> list[float]:
    """Generate embeddings for repository using LangChain."""
    from langchain.embeddings import OpenAIEmbeddings  # or Anthropic, etc.

    embeddings = OpenAIEmbeddings()
    repo_text = f"{repo_data['name']}: {repo_data['description']}"
    return embeddings.embed_query(repo_text)


@task(
    name="store-repository",
    tags=["storage", "collection"]
)
def store_repository_task(
    repo_data: dict,
    embeddings: list[float],
    knowledge_base_path: str
) -> str:
    """Store repository in hybrid storage (File + ChromaDB + NetworkX)."""
    from curator.knowledge.store import KnowledgeStore

    store = KnowledgeStore(knowledge_base_path)
    return store.add_repository(repo_data, embeddings)
```

### Step 4: Create Collection Flow (1 hour)
```python
# curator/pipeline/flows.py

@flow(name="collect-repositories", log_prints=True)
def collect_repositories_flow(
    topic: Optional[str] = None,
    specific_repos: Optional[list[str]] = None,
    limit: int = 100,
    min_stars: int = 100,
    language: Optional[str] = None,
    refresh_existing: bool = False,
    use_git_clone: bool = False
) -> dict:
    """Collect repositories and build knowledge base."""

    results = {
        "collected_count": 0,
        "updated_count": 0,
        "skipped_count": 0,
        "new_topics_count": 0,
        "errors": []
    }

    # Step 1: Get repositories to collect
    if specific_repos:
        repos = [{"full_name": r} for r in specific_repos]
    elif topic:
        repos = search_github_repos_task(topic, limit, min_stars, language)
    else:
        raise ValueError("Must provide either topic or specific_repos")

    # Step 2: Process each repository (parallel)
    for repo in repos:
        try:
            # Analyze repository
            repo_data = analyze_repository_task(
                repo["full_name"],
                use_git_clone=use_git_clone
            )

            # Generate embeddings
            embeddings = generate_embeddings_task(repo_data)

            # Store in knowledge base
            store_repository_task(repo_data, embeddings, ".curator/knowledge")

            results["collected_count"] += 1

        except Exception as e:
            results["errors"].append({"repo": repo["full_name"], "error": str(e)})

    return results
```

### Step 5: Integration with Hybrid Storage (2 hours)

Create unified knowledge store interface:
```python
# curator/knowledge/store.py

from chromadb import Client as ChromaClient
import networkx as nx
from pathlib import Path
import json

class KnowledgeStore:
    """Unified interface for hybrid storage (File + ChromaDB + NetworkX)."""

    def __init__(self, base_path: str = ".curator/knowledge"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        # File storage
        self.repos_file = self.base_path / "repositories.jsonl"
        self.metadata_file = self.base_path / "metadata.json"

        # Vector storage (ChromaDB)
        self.chroma_client = ChromaClient()
        self.collection = self.chroma_client.get_or_create_collection("repositories")

        # Graph storage (NetworkX)
        self.graph = nx.DiGraph()

    def add_repository(self, repo_data: dict, embeddings: list[float]) -> str:
        """Add repository to all storage layers."""
        repo_id = repo_data["full_name"]

        # 1. File storage (JSONL)
        with open(self.repos_file, "a") as f:
            json.dump(repo_data, f)
            f.write("\n")

        # 2. Vector storage (ChromaDB)
        self.collection.add(
            ids=[repo_id],
            embeddings=[embeddings],
            metadatas=[{
                "name": repo_data["name"],
                "stars": repo_data["stars"],
                "language": repo_data.get("language", "unknown")
            }],
            documents=[repo_data["description"]]
        )

        # 3. Graph storage (NetworkX)
        self.graph.add_node(repo_id, **repo_data)
        for topic in repo_data.get("topics", []):
            self.graph.add_edge(repo_id, f"topic:{topic}", relation="has_topic")

        # Update metadata
        self._update_metadata()

        return repo_id

    def find_similar(self, query: str, limit: int = 10) -> list[dict]:
        """Semantic search using ChromaDB."""
        results = self.collection.query(
            query_texts=[query],
            n_results=limit
        )
        return results

    def find_related_topics(self, repo_id: str) -> list[str]:
        """Find related topics using graph."""
        if repo_id not in self.graph:
            return []
        return [
            n.replace("topic:", "")
            for n in self.graph.neighbors(repo_id)
            if n.startswith("topic:")
        ]
```

### Step 6: Testing (2 hours)
```python
# tests/test_collect_command.py

def test_collect_by_topic():
    """Test collecting repositories by topic."""
    result = collect_repositories(
        topic="machine-learning",
        limit=10,
        min_stars=100
    )
    assert result["collected_count"] > 0
    assert result["collected_count"] <= 10


def test_collect_specific_repos():
    """Test collecting specific repositories."""
    result = collect_repositories(
        specific_repos=["fastapi/fastapi", "tiangolo/typer"],
        limit=100
    )
    assert result["collected_count"] == 2


def test_collect_refresh_mode():
    """Test refresh existing repositories."""
    # First collection
    result1 = collect_repositories(topic="async", limit=5)

    # Refresh
    result2 = collect_repositories(topic="async", limit=5, refresh_existing=True)

    assert result2["updated_count"] > 0


def test_hybrid_storage_integration():
    """Test all storage layers are updated."""
    store = KnowledgeStore()

    repo_data = {
        "full_name": "test/repo",
        "name": "repo",
        "description": "Test repository",
        "stars": 100,
        "topics": ["test", "sample"]
    }
    embeddings = [0.1] * 1536  # Mock embedding

    repo_id = store.add_repository(repo_data, embeddings)

    # Verify file storage
    assert store.repos_file.exists()

    # Verify vector storage
    results = store.collection.get(ids=[repo_id])
    assert len(results["ids"]) == 1

    # Verify graph storage
    assert repo_id in store.graph
    assert len(store.find_related_topics(repo_id)) == 2
```

## Timeline

| Task | Duration | Dependencies |
|------|----------|--------------|
| Extract original code | 30 min | - |
| Update for Prefect + LangChain | 2 hours | LLM abstraction Phase 1 |
| Create Prefect tasks | 2 hours | Prefect pipeline Phase 1 |
| Create collection flow | 1 hour | Tasks complete |
| Hybrid storage integration | 2 hours | ChromaDB + NetworkX setup |
| Testing | 2 hours | All above |
| Documentation | 1 hour | All above |
| **Total** | **10.5 hours** | **~2 days** |

## Dependencies

- ✅ Prefect pipeline (Phase 1 complete)
- 🚧 LangChain integration (planned - Phase 1)
- 🚧 ChromaDB setup (planned - Phase 2)
- 🚧 NetworkX setup (planned - Phase 3)
- 🚧 Unified KnowledgeStore (planned - Phase 4)

Can implement in **degraded mode** with file storage only, but full value requires hybrid storage for semantic search and relationship discovery.

## Success Criteria

- [ ] Command works with topic-based search
- [ ] Command works with specific repository list
- [ ] Refresh mode updates existing repositories
- [ ] Language filtering works correctly
- [ ] Knowledge base structure maintained (JSONL + metadata)
- [ ] Embeddings generated and stored (ChromaDB)
- [ ] Graph relationships built (NetworkX)
- [ ] Progress reporting during collection
- [ ] Error handling for rate limits / API failures
- [ ] All tests pass
- [ ] Documentation updated

## Future Enhancements

1. **Incremental Updates**: Daily/weekly cron job to refresh knowledge base
2. **Topic Discovery**: Automatically discover related topics during collection
3. **Quality Filtering**: ML-based repository quality assessment
4. **Duplicate Detection**: Identify and merge similar repositories
5. **Export Formats**: Export knowledge base to various formats (CSV, SQL, etc.)
6. **Batch Collection**: Collect from multiple topics in parallel
7. **Web UI**: Visual interface for browsing/managing knowledge base

## Migration Path

### Phase 1: Restore with File Storage (Week 1)
- Implement collect command with current file-based storage
- JSONL + metadata.json structure
- No embeddings or graph yet

### Phase 2: Add ChromaDB (Week 2)
- Generate embeddings during collection
- Store in ChromaDB for semantic search
- Migrate existing repositories to ChromaDB

### Phase 3: Add NetworkX (Week 3)
- Build graph relationships during collection
- Track topic co-occurrence
- Enable graph queries

### Phase 4: Unified Interface (Week 4)
- Single KnowledgeStore API
- Intelligent query routing
- Hybrid queries (semantic + graph)
