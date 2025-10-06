# Hybrid Knowledge Storage Architecture

## Executive Summary

Design for a **hybrid storage system** combining:
- **File-based caching** (current) - Fast, simple, version-controlled
- **Vector database** - Semantic search and similarity
- **Graph database** - Relationship queries and pattern discovery

This enables powerful capabilities like semantic repo search, topic clustering, and pattern mining while maintaining the simplicity of file-based caching for simple lookups.

---

## Current State Analysis

### What We Have Now

**File Structure:**
```
.curator/knowledge/
├── metadata.json              # Stats: 50 repos, 62 topics
├── repositories.jsonl         # One repo per line (JSONL)
├── topic_patterns.json        # Topic → features/keywords/examples
└── topic_cooccurrence.json    # Topic pair statistics
```

**Data Model:**
1. **Repository data** (JSONL):
   - Full name, topics, features, language, stars
   - Features: has_readme, readme_length, has_tests, etc.

2. **Topic patterns** (JSON):
   - Per topic: common_features, common_keywords, example_repos
   - Used for pattern-based search heuristics

3. **Topic co-occurrence** (JSON):
   - Which topics appear together
   - Frequency-based

### Current Strengths ✅

1. **Simple** - Just JSON files, easy to inspect/debug
2. **Version controlled** - Can track in git
3. **Fast for exact lookups** - No database overhead
4. **Portable** - Works anywhere, no services needed
5. **Transparent** - Human-readable

### Current Limitations ❌

1. **No semantic search** - Can't find "similar" repos
2. **Limited pattern mining** - Hard to discover implicit relationships
3. **No similarity metrics** - Can't cluster or recommend
4. **Scalability** - JSONL parsing slow at 10K+ repos
5. **Complex queries** - Need to write custom code for each query type

---

## Proposed Hybrid Architecture

### Three-Layer Storage Model

```
┌─────────────────────────────────────────────────────────────┐
│                    Query Layer (Unified API)                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────┼─────────────────────┐
        ↓                     ↓                     ↓
┌───────────────┐    ┌────────────────┐    ┌──────────────┐
│  File Cache   │    │  Vector Store  │    │  Graph DB    │
│  (Current)    │    │  (Semantic)    │    │ (Relations)  │
└───────────────┘    └────────────────┘    └──────────────┘
        ↓                     ↓                     ↓
  Fast Lookups       Similarity Search      Pattern Discovery
```

### Layer 1: File Cache (Keep Current)

**Use for:**
- Fast exact lookups by repo name
- Recent query caching (intent structures, evaluations)
- Prefect result storage
- Version-controlled knowledge

**Technology:** Current JSON/JSONL files

**Why keep it:**
- Already works well
- Git-trackable
- Zero infrastructure
- Great for development/debugging

### Layer 2: Vector Database (NEW)

**Use for:**
- Semantic search: "Find repos similar to FastAPI"
- Topic discovery: "What topics cluster together?"
- Embedding-based recommendations
- Fuzzy matching on descriptions

**Technology Options:**

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| **ChromaDB** | 🟢 Lightweight<br>🟢 Local-first<br>🟢 Python-native<br>🟢 Easy setup | 🔴 Less mature | **Best for now** |
| **Qdrant** | 🟢 Fast<br>🟢 Production-ready<br>🟢 Good Python support | 🟡 Requires server | Good for scale |
| **Weaviate** | 🟢 Feature-rich<br>🟢 GraphQL API | 🔴 Heavy<br>🔴 Complex setup | Overkill |
| **FAISS** | 🟢 Blazing fast<br>🟢 Facebook-backed | 🔴 Low-level<br>🔴 No DB features | For experts |

**Recommendation: ChromaDB**
- Embeds in-process (like SQLite)
- Persists to disk (.curator/chroma/)
- Simple Python API
- Can upgrade to client-server later

**What to store:**
```python
# Repo embeddings
collection.add(
    documents=[repo.full_name + " " + repo.description],
    metadatas=[{
        "full_name": repo.full_name,
        "topics": repo.topics,
        "stars": repo.stars,
        "language": repo.language
    }],
    ids=[repo.full_name]
)

# Topic embeddings (for clustering)
collection.add(
    documents=[topic_name + " " + topic_description],
    metadatas=[{
        "topic": topic_name,
        "common_keywords": topic.keywords,
        "repo_count": len(topic.repos)
    }],
    ids=[topic_name]
)
```

**Example Queries:**
```python
# Find similar repos
results = collection.query(
    query_texts=["async web framework like FastAPI"],
    n_results=10
)

# Find repos by topic embedding
results = collection.query(
    query_texts=["machine learning visualization"],
    where={"language": "Python", "stars": {"$gte": 100}}
)
```

### Layer 3: Graph Database (NEW)

**Use for:**
- Relationship queries: "Which repos share contributors?"
- Pattern discovery: "Common architectural patterns?"
- Influence graphs: "What repos depend on this?"
- Co-occurrence analysis: "What topics always appear together?"

**Technology Options:**

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| **Neo4j** | 🟢 Industry standard<br>🟢 Cypher query language<br>🟢 Great tools | 🔴 Heavy (JVM)<br>🔴 Licensing complexity | Powerful but heavy |
| **NetworkX** | 🟢 Pure Python<br>🟢 Simple<br>🟢 Great for analysis | 🔴 In-memory only<br>🔴 Not persistent | Good for prototyping |
| **TigerGraph** | 🟢 Very fast<br>🟢 Graph analytics | 🔴 Complex setup<br>🔴 Overkill | Too much |
| **Custom (NetworkX + pickle)** | 🟢 Lightweight<br>🟢 Flexible | 🔴 DIY persistence | **Best for now** |

**Recommendation: NetworkX + pickle**
- Start simple: use NetworkX for graph operations
- Persist to `.curator/graph.pkl`
- Migrate to Neo4j if/when needed

**What to store:**
```python
import networkx as nx

G = nx.DiGraph()

# Nodes: Repos, Topics, Features
G.add_node("fastapi/fastapi", type="repo", stars=90405, language="Python")
G.add_node("async", type="topic", frequency=50)
G.add_node("has_tests", type="feature")

# Edges: Relationships
G.add_edge("fastapi/fastapi", "async", relation="has_topic", weight=1.0)
G.add_edge("fastapi/fastapi", "has_tests", relation="has_feature", present=True)
G.add_edge("async", "asyncio", relation="cooccurs_with", frequency=45)

# Persist
nx.write_gpickle(G, ".curator/graph.pkl")
```

**Example Queries:**
```python
# Find all repos with topic "async" AND "fastapi"
repos_with_both = set(G.neighbors("async")) & set(G.neighbors("fastapi"))

# Find central topics (PageRank)
centrality = nx.pagerank(G)
top_topics = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:10]

# Find repos similar in structure (common features)
def similar_repos(repo_name, top_n=5):
    features = set(G.neighbors(repo_name))
    similar = []
    for node in G.nodes():
        if G.nodes[node].get("type") == "repo" and node != repo_name:
            other_features = set(G.neighbors(node))
            similarity = len(features & other_features) / len(features | other_features)
            similar.append((node, similarity))
    return sorted(similar, key=lambda x: x[1], reverse=True)[:top_n]
```

---

## Unified Query API

**Single interface for all storage layers:**

```python
from curator.knowledge import KnowledgeStore

store = KnowledgeStore()

# File cache (fast exact lookup)
repo = store.get_repo("fastapi/fastapi")  # From JSONL

# Vector search (semantic)
similar = store.find_similar_repos("async web framework", limit=10)  # From ChromaDB

# Graph queries (relationships)
related_topics = store.find_related_topics("async", depth=2)  # From NetworkX

# Hybrid query (combines all)
results = store.search(
    semantic_query="lightweight async framework",
    filters={"stars": {"min": 1000}, "has_tests": True},
    include_similar_topics=True
)
```

---

## Data Flow

### Ingestion Pipeline

```
GitHub API → Repository Analysis
                    ↓
        ┌───────────┴──────────┐
        ↓                      ↓
   File Cache            Vector DB
   (JSONL write)       (Embed + Store)
        ↓                      ↓
   Graph DB ←──────────────────┘
   (Build relationships)
```

### Query Pipeline

```
User Query
    ↓
Parse Intent
    ↓
┌───┴───┐
│Router │ → Exact match?    → File Cache
└───┬───┘   Semantic?       → Vector DB
    ↓       Relationships?  → Graph DB
Combined Results
    ↓
Return to User
```

---

## Migration Strategy

### Phase 1: Add Vector DB (Week 1)

1. **Install ChromaDB**
   ```bash
   pip install chromadb
   ```

2. **Create embedding service**
   ```python
   # curator/knowledge/embeddings.py
   import chromadb

   client = chromadb.PersistentClient(path=".curator/chroma")
   collection = client.get_or_create_collection("repositories")
   ```

3. **Populate from existing JSONL**
   ```python
   # One-time migration
   with open(".curator/knowledge/repositories.jsonl") as f:
       for line in f:
           repo = json.loads(line)
           collection.add(
               documents=[f"{repo['full_name']}: {' '.join(repo['topics'])}"],
               metadatas=[repo],
               ids=[repo['full_name']]
           )
   ```

4. **Add semantic search**
   ```python
   def find_similar_repos(query: str, limit: int = 10):
       results = collection.query(
           query_texts=[query],
           n_results=limit
       )
       return results['metadatas'][0]
   ```

### Phase 2: Add Graph DB (Week 2)

1. **Install NetworkX**
   ```bash
   pip install networkx
   ```

2. **Build graph from existing data**
   ```python
   import networkx as nx

   G = nx.DiGraph()

   # Load from JSONL
   with open(".curator/knowledge/repositories.jsonl") as f:
       for line in f:
           repo = json.loads(line)
           G.add_node(repo['full_name'], type='repo', **repo)

           for topic in repo['topics']:
               G.add_node(topic, type='topic')
               G.add_edge(repo['full_name'], topic, relation='has_topic')

   # Persist
   nx.write_gpickle(G, ".curator/graph.pkl")
   ```

3. **Add graph queries**
   ```python
   def find_topic_clusters():
       # Community detection
       communities = nx.community.greedy_modularity_communities(G.to_undirected())
       return list(communities)
   ```

### Phase 3: Unified API (Week 3)

1. **Create KnowledgeStore class**
   ```python
   class KnowledgeStore:
       def __init__(self):
           self.file_cache = FileCache()
           self.vector_db = ChromaDB()
           self.graph_db = GraphDB()

       def search(self, **kwargs):
           # Route to appropriate backend(s)
           ...
   ```

2. **Update existing code**
   - Replace direct JSONL reads with `store.get_repo()`
   - Add semantic search to adaptive search
   - Use graph for pattern discovery in reflection

---

## Use Cases Unlocked

### 1. Semantic Repository Discovery
**Before:**
```python
# Had to know exact topic names
repos = [r for r in all_repos if "fastapi" in r.topics]
```

**After:**
```python
# Natural language search
repos = store.find_similar_repos(
    "lightweight asynchronous web framework for Python APIs",
    limit=20
)
```

### 2. Topic Clustering
**Before:**
```
# Manual analysis of topic_patterns.json
```

**After:**
```python
# Automatic clustering
clusters = store.find_topic_clusters()
# Result: [["async", "asyncio", "aiohttp"], ["fastapi", "uvicorn", "starlette"], ...]
```

### 3. Architectural Pattern Discovery
**Before:**
```
# Not possible
```

**After:**
```python
# Find repos with similar feature profiles
pattern = store.find_architectural_pattern(
    features=["has_tests", "has_docs", "has_examples", "has_architecture_md"]
)
# Returns: Repos that follow "well-documented" pattern
```

### 4. Recommendation System
**Before:**
```
# Not possible
```

**After:**
```python
# "Users who liked FastAPI also liked..."
recommended = store.recommend_similar(
    repo="fastapi/fastapi",
    based_on=["topics", "features", "architecture"],
    limit=5
)
```

---

## Storage Comparison

| Feature | File Cache | Vector DB | Graph DB |
|---------|-----------|-----------|----------|
| **Exact lookup** | ⚡ Instant | ⚠️ Slower | ❌ Not ideal |
| **Semantic search** | ❌ No | ✅ Perfect | ⚠️ Limited |
| **Relationships** | ❌ No | ⚠️ Limited | ✅ Perfect |
| **Scalability** | ⚠️ Linear | ✅ Log(n) | ⚠️ Varies |
| **Setup complexity** | ✅ None | ✅ Easy | ⚠️ Medium |
| **Storage size** | ✅ Small | ⚠️ Medium | ✅ Small |
| **Git-trackable** | ✅ Yes | ❌ No | ⚠️ Possible |
| **Query flexibility** | ❌ Low | ⚠️ Medium | ✅ High |

---

## Recommendations

### Immediate (Do Now)
1. **Add ChromaDB** for semantic search
   - Low effort, high value
   - Enables natural language queries
   - Improves adaptive search quality

2. **Keep file cache** for:
   - Exact lookups (repo by name)
   - Prefect results
   - Development debugging

### Near-term (Next Month)
3. **Add NetworkX graph** for:
   - Topic clustering
   - Pattern discovery in reflection module
   - Architectural similarity

### Future (When Needed)
4. **Upgrade to Neo4j** if:
   - Graph queries become slow (>10K repos)
   - Need multi-user access
   - Want advanced graph analytics

5. **Upgrade to Qdrant** if:
   - ChromaDB becomes slow
   - Need distributed deployment
   - Require production SLAs

---

## Implementation Estimate

| Phase | Effort | Value | Priority |
|-------|--------|-------|----------|
| ChromaDB integration | 1-2 days | High | **P0** |
| Semantic search API | 1 day | High | **P0** |
| NetworkX graph | 2-3 days | Medium | **P1** |
| Graph query API | 1-2 days | Medium | **P1** |
| Unified KnowledgeStore | 2 days | High | **P1** |
| Neo4j migration | 1 week | Low (if needed) | **P2** |

**Total for hybrid system: ~1-2 weeks**

---

## Conclusion

A **hybrid approach** is ideal:
- Keep file cache for simplicity
- Add ChromaDB for semantic search
- Add NetworkX for relationships
- Upgrade selectively when needed

This gives you **the best of all worlds**:
- 🚀 Performance (file cache for hot paths)
- 🧠 Intelligence (vector search for discovery)
- 🔗 Insights (graph for patterns)
- 💡 Simplicity (start small, grow as needed)

**Recommendation**: Start with ChromaDB this week!
