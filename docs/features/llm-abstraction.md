# LLM Abstraction Layer: LiteLLM vs LangChain

## TL;DR Recommendation

**Use LangChain** because:
1. ✅ Integrates perfectly with ChromaDB (vector store)
2. ✅ Provides embeddings for semantic search
3. ✅ Supports all providers (Anthropic/OpenAI/Ollama/Google)
4. ✅ Future-proof for RAG and agents
5. ✅ One dependency solves multiple problems

---

## The Full Picture

Your request to make LLM provider configurable **ties directly** to your knowledge storage decision. Here's why:

### Current Pain Points

1. **LLM Provider**: Locked to Anthropic
2. **Knowledge Storage**: Just JSON files, no semantic search
3. **Search Quality**: Keyword-based only

### What You Actually Need

Not just provider swapping, but:
- **Embeddings** for semantic search (ChromaDB needs this)
- **Multiple providers** (Anthropic/OpenAI/Ollama)
- **Future RAG** (analyze repo docs with context)

---

## Option 1: LiteLLM (Simple Path)

### What You Get
```python
import litellm

# Just provider swapping
response = litellm.completion(
    model="claude-sonnet-4-5" or "gpt-4o" or "ollama/llama3.1",
    messages=[{"role": "user", "content": prompt}]
)
```

### Pros
- ✅ Minimal code changes
- ✅ Lightweight (small dependency)
- ✅ Drop-in replacement

### Cons
- ❌ **No embeddings** - need separate library for ChromaDB
- ❌ **No RAG support** - would need to build yourself
- ❌ **No caching** - would need to implement
- ❌ **Two dependencies**: LiteLLM + sentence-transformers (for embeddings)

### What You'd Need to Add

```python
# For LLM calls
import litellm

# For embeddings (separate!)
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')

# Now you have TWO libraries to configure
```

---

## Option 2: LangChain (Complete Path)

### What You Get
```python
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.llms import Ollama
from langchain_chroma import Chroma

# LLM swapping
llm = ChatAnthropic(model="claude-sonnet-4-5")
# or
llm = ChatOpenAI(model="gpt-4o")
# or
llm = Ollama(model="llama3.1")

# Embeddings (SAME ecosystem)
embeddings = OpenAIEmbeddings()  # or AnthropicEmbeddings, etc.

# Vector store (SAME ecosystem)
vectorstore = Chroma(
    embedding_function=embeddings,
    persist_directory=".curator/chroma"
)

# Future: RAG (SAME ecosystem)
from langchain.chains import RetrievalQA
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vectorstore.as_retriever()
)
```

### Pros
- ✅ **Unified ecosystem** - LLMs + embeddings + vector stores
- ✅ **Native ChromaDB integration**
- ✅ **Built-in caching** (via LangChain cache)
- ✅ **RAG ready** - analyze repo docs with context
- ✅ **Agent framework** - future GitHub API tool use
- ✅ **One dependency** for everything

### Cons
- ⚠️ Heavier than LiteLLM
- ⚠️ More to learn (but better docs)
- ⚠️ Some breaking changes between versions (stabilizing)

---

## Decision Matrix

| Need | LiteLLM | LangChain | Winner |
|------|---------|-----------|--------|
| **Provider swapping** | ✅ Excellent | ✅ Excellent | Tie |
| **Embeddings** | ❌ Need extra lib | ✅ Built-in | **LangChain** |
| **Vector DB integration** | ❌ DIY | ✅ Native | **LangChain** |
| **RAG capabilities** | ❌ DIY | ✅ Built-in | **LangChain** |
| **Simplicity** | ✅ Lightweight | ⚠️ More complex | **LiteLLM** |
| **Total dependencies** | 2+ (LiteLLM + embeddings) | 1 (LangChain) | **LangChain** |
| **Future-proof** | ⚠️ Limited | ✅ Full featured | **LangChain** |

---

## The Synergy: LangChain + ChromaDB

Your two questions are actually **one problem**:

### Combined Architecture

```python
# curator/llm/provider.py
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.llms import Ollama
from langchain_chroma import Chroma

class LLMProvider:
    """Unified LLM and embedding provider."""

    def __init__(self, provider="anthropic", model=None):
        if provider == "anthropic":
            self.llm = ChatAnthropic(model=model or "claude-sonnet-4-5")
            self.embeddings = OpenAIEmbeddings()  # Anthropic doesn't have embeddings yet
        elif provider == "openai":
            self.llm = ChatOpenAI(model=model or "gpt-4o")
            self.embeddings = OpenAIEmbeddings()
        elif provider == "ollama":
            self.llm = Ollama(model=model or "llama3.1")
            self.embeddings = OllamaEmbeddings()

    def complete(self, messages):
        return self.llm.invoke(messages)

    def embed(self, text):
        return self.embeddings.embed_query(text)

# curator/knowledge/store.py
class KnowledgeStore:
    """Unified knowledge storage with semantic search."""

    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

        # Vector store (uses provider's embeddings)
        self.vectorstore = Chroma(
            persist_directory=".curator/chroma",
            embedding_function=llm_provider.embeddings
        )

    def add_repo(self, repo):
        # Automatically embeds using configured provider
        self.vectorstore.add_texts(
            texts=[f"{repo.full_name}: {' '.join(repo.topics)}"],
            metadatas=[repo.to_dict()]
        )

    def find_similar(self, query: str, limit: int = 10):
        # Semantic search using embeddings
        return self.vectorstore.similarity_search(query, k=limit)
```

### Configuration

```yaml
# config/curator.yaml
llm:
  # Choose provider
  provider: "anthropic"  # or "openai", "ollama", "google"

  # Provider-specific models
  models:
    anthropic: "claude-sonnet-4-5-20250929"
    openai: "gpt-4o"
    ollama: "llama3.1"
    google: "gemini-pro"

  # Embedding settings
  embeddings:
    provider: "openai"  # Most reliable for now
    model: "text-embedding-3-small"
    cache_embeddings: true

vector_store:
  enabled: true
  backend: "chroma"
  persist_directory: ".curator/chroma"
```

### Usage

```python
# Configure once
provider = LLMProvider(
    provider=config['llm']['provider'],
    model=config['llm']['models'][config['llm']['provider']]
)

# Use everywhere
intent = await provider.complete([
    {"role": "user", "content": "Structure this theme: ML tools"}
])

# Semantic search (uses same provider's embeddings)
store = KnowledgeStore(provider)
similar_repos = store.find_similar("async web framework")
```

---

## Use Cases Enabled by LangChain

### 1. Semantic Repository Search
```python
from langchain_chroma import Chroma

# Natural language search
vectorstore = Chroma(persist_directory=".curator/chroma")
results = vectorstore.similarity_search(
    "lightweight async web framework like Flask but modern",
    k=10
)
```

### 2. RAG for Documentation Analysis
```python
from langchain.chains import RetrievalQA

# Analyze README with context
qa = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vectorstore.as_retriever(),
    return_source_documents=True
)

answer = qa.invoke({
    "query": "Does this repo have good testing practices?"
})
```

### 3. Agent-Based GitHub API Exploration
```python
from langchain.agents import initialize_agent, Tool

# GitHub API as a tool
tools = [
    Tool(
        name="GitHub Search",
        func=github_search,
        description="Search GitHub repositories"
    ),
    Tool(
        name="Analyze Repo",
        func=analyze_repo,
        description="Get detailed repo analysis"
    )
]

agent = initialize_agent(tools, llm, agent="zero-shot-react-description")
result = agent.invoke("Find popular async Python frameworks and compare them")
```

### 4. Multi-Step Curation with Memory
```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory()

# Iterative refinement
chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=vectorstore.as_retriever(),
    memory=memory
)

# First query
chain.invoke({"question": "Find async web frameworks"})

# Follow-up (remembers context)
chain.invoke({"question": "Which ones have the best documentation?"})
```

---

## Migration Path

### Week 1: Foundation (LangChain + Basic Provider Swapping)
```bash
pip install langchain langchain-anthropic langchain-openai langchain-community
```

```python
# Minimal change to existing code
from langchain_anthropic import ChatAnthropic

# Replace anthropic.Anthropic() with:
llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")

# Same API, more flexible
response = llm.invoke([{"role": "user", "content": prompt}])
```

### Week 2: Add Embeddings + ChromaDB
```bash
pip install chromadb langchain-chroma
```

```python
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

embeddings = OpenAIEmbeddings()
vectorstore = Chroma(
    persist_directory=".curator/chroma",
    embedding_function=embeddings
)

# Migrate existing JSONL
for repo in existing_repos:
    vectorstore.add_texts(
        texts=[repo.description],
        metadatas=[repo.to_dict()],
        ids=[repo.full_name]
    )
```

### Week 3: Unified API
```python
# curator/llm/factory.py
def get_llm_provider(config):
    provider = config['llm']['provider']

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=config['llm']['models']['anthropic'])
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=config['llm']['models']['openai'])
    elif provider == "ollama":
        from langchain_community.llms import Ollama
        return Ollama(model=config['llm']['models']['ollama'])
    else:
        raise ValueError(f"Unknown provider: {provider}")
```

---

## Cost Comparison

### LiteLLM Approach
```
LiteLLM:                  Free
Sentence Transformers:    Free (local models)
Implementation time:      ~3 days
Maintenance:             Medium (two systems)
```

### LangChain Approach
```
LangChain:               Free
ChromaDB:                Free
OpenAI Embeddings:       ~$0.02 per 1M tokens (very cheap)
Implementation time:     ~4 days (slightly more setup)
Maintenance:             Low (integrated ecosystem)
Future capabilities:     High (RAG, agents, etc.)
```

**Winner**: LangChain (slightly more upfront, much better long-term)

---

## Final Recommendation

### Use **LangChain** Because:

1. **Solves both problems**: LLM swapping + semantic search
2. **One ecosystem**: Embeddings + vector DB + LLMs unified
3. **Future-proof**: Ready for RAG, agents, advanced use cases
4. **Better integration**: ChromaDB is a LangChain first-class citizen
5. **Actual use case**: You NEED embeddings for semantic search anyway

### Migration Order:

1. **This week**: Add LangChain for provider abstraction
2. **Next week**: Add ChromaDB with LangChain embeddings
3. **Week 3**: NetworkX graph for relationships
4. **Week 4**: RAG for README analysis (optional but cool)

### Configuration:

```yaml
# config/curator.yaml
llm:
  provider: "anthropic"  # Easy to change!
  fallback: "openai"     # Automatic fallback

embeddings:
  provider: "openai"     # Best quality/price
  model: "text-embedding-3-small"

storage:
  vector_db: "chroma"
  graph_db: "networkx"
  file_cache: true  # Keep for exact lookups
```

**Bottom line**: LangChain gives you MORE than just LLM swapping - it's your gateway to semantic search, RAG, and intelligent curation. The extra complexity is worth it for the capabilities unlocked.
