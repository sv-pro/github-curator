# `curator review` Command

Quick review updates for tracked repositories.

## What It Does

The `curator review` command is a lighter alternative to `curator curate-tracked`:

1. **Pulls all branches** from upstream (git fetch + pull all)
2. **Evaluates the main branch** with your theme
3. **Updates REVIEW.md** with fresh LLM-generated content
4. **Does NOT modify CURATION.md** (history unchanged)
5. **Creates commit + tag** on curation branch (with `review-` prefix)

## When to Use

**Use `curator review`** when:
- You want to refresh a review with a new perspective/theme
- The repo has been updated and you want a new review
- You're iterating on review content without formal curation
- You want lightweight tracking without full history

**Use `curator curate-tracked`** when:
- You want a formal evaluation entry
- You want to append to CURATION.md history
- You're tracking evolution over time with multiple themes
- This is a milestone evaluation

## Usage

```bash
curator review <org/repo> "<theme>"
```

### Examples

```bash
# Quick review update
curator review fastapi/fastapi "Modern Python web frameworks"

# After upstream updates
curator review pallets/flask "Beginner-friendly frameworks 2025"

# Different perspective on same repo
curator review django/django "Enterprise-ready frameworks"
```

## What Happens

### Step-by-Step

```bash
$ curator review fastapi/fastapi "Modern async frameworks"

🔄 Reviewing tracked repository: fastapi/fastapi
   Theme: Modern async frameworks

📥 Syncing all branches from upstream...
   ✓ Updated branches: main, docs-update

🧠 Initializing evaluation...
📋 Structuring intent...
   Created 5 evaluation dimensions

📊 Fetching repository data...
🔍 Analyzing repository content...
🤖 Evaluating with Claude...
   ✓ Score: 9.2
   ✓ Confidence: 0.92

📝 Generating review...
   ✓ Updated .curator/REVIEW.md
   ✓ Created commit and tag: review-001-20251010

✨ Review complete!

View review:
   cat ~/.github-curator/tracked/fastapi/fastapi/.curator/REVIEW.md

Note: CURATION.md history was not modified.
      Use 'curator curate-tracked' to add full curation entry.
```

### Git Operations

```bash
# What happens in the tracked repo:
cd ~/.github-curator/tracked/org/repo

# 1. Fetch all branches
git fetch --all --tags

# 2. For each branch (main, develop, etc.):
git checkout <branch>
git pull origin <branch>

# 3. Switch to curation branch
git checkout curation

# 4. Update REVIEW.md (CURATION.md untouched)
echo "..." > .curator/REVIEW.md

# 5. Commit and tag
git add .curator/REVIEW.md
git commit -m "review: Modern async frameworks"
git tag -a review-001-20251010 -m "Review: Modern async frameworks"
```

## File Changes

**Before:**
```
.curator/
├── CURATION.md    (history from previous curations)
└── REVIEW.md      (old review)
```

**After:**
```
.curator/
├── CURATION.md    (unchanged - history preserved)
└── REVIEW.md      (NEW fresh review with updated content)
```

## Tag Naming

- **Curation tags**: `curation-001-20251010`, `curation-002-20251015`, ...
- **Review tags**: `review-001-20251010`, `review-002-20251012`, ...

Separate numbering allows you to mix curations and reviews:
```bash
git tag -l
# curation-001-20251001
# review-001-20251005
# review-002-20251007
# curation-002-20251010
# review-003-20251011
```

## Comparison: `review` vs `curate-tracked`

| Feature | `curator review` | `curator curate-tracked` |
|---------|------------------|--------------------------|
| Pulls all branches | ✅ Yes (fetch --all) | ⚠️ Only main branch |
| Updates REVIEW.md | ✅ Yes (overwrites) | ✅ Yes (overwrites) |
| Updates CURATION.md | ❌ No | ✅ Yes (appends) |
| Creates commit | ✅ Yes | ✅ Yes |
| Creates tag | ✅ Yes (review-*) | ✅ Yes (curation-*) |
| Use case | Quick updates | Formal curation |

## Options

```bash
curator review <repo> "<theme>" [OPTIONS]

Options:
  --base-path PATH       Custom tracked repos directory
  --config PATH          Config file (default: config/curator.yaml)
  --use-git-clone        Clone repo locally for deeper analysis
  -h, --help            Show help message
```

## Typical Workflow

### Initial Setup
```bash
# Track a repo
curator track https://github.com/fastapi/fastapi

# First formal curation
curator curate-tracked fastapi/fastapi "Initial evaluation"
```

### Ongoing Reviews
```bash
# Quick review updates (weekly/monthly)
curator review fastapi/fastapi "Q1 2025 check-in"
curator review fastapi/fastapi "Post v1.0 release"
curator review fastapi/fastapi "Performance improvements"

# Formal milestone curations (quarterly)
curator curate-tracked fastapi/fastapi "Q1 2025 comprehensive eval"
```

### Result
- **CURATION.md**: Milestone evaluations (3-4 per year)
- **REVIEW.md**: Always current (updated weekly/monthly)
- **Git history**: Full timeline of both

## Benefits

1. **Keep REVIEW.md fresh** without cluttering CURATION.md
2. **Sync all branches** automatically
3. **Faster iterations** on review content
4. **Separate concerns**: Reviews vs formal curations
5. **Full traceability**: Every review is tagged and committed

## See Also

- `curator track` - Start tracking a repo
- `curator curate-tracked` - Full curation with history
- `curator list-tracked` - Show tracked repos
- [REPO_TRACKING.md](REPO_TRACKING.md) - Full tracking documentation
