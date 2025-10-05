# GitHub Curator - Quick Start

Get up and running with GitHub Curator in 5 minutes.

## 1. Install

```bash
git clone https://github.com/IntentHub/github-curator.git
cd github-curator
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .
```

## 2. Configure

```bash
cp .env.example .env
```

Edit `.env`:
```env
ANTHROPIC_API_KEY=your_anthropic_key
GITHUB_TOKEN=your_github_token
```

## 3. Verify

```bash
python -m curator setup
```

## 4. Run Your First Curation

```bash
python -m curator curate "Python CLI tools for developers" --limit 10
```

## 5. View Results

Check the `output/` directory:
- `reports/*.md` - Markdown report
- `reports/*.html` - Interactive trace viewer (open in browser)
- `summary.json` - Quick overview
- `evaluations/*.json` - Detailed evaluations

## Common Commands

```bash
# Basic curation
curator curate "AI agents with tool use"

# With options
curator curate "machine learning libraries" \
  --focus "visualization" \
  --exclude "unmaintained" \
  --limit 20 \
  --min-stars 100

# View previous results
curator show <intent-id>

# Check configuration
curator validate-config
```

## What's Happening?

1. **Intent Structuring** - Your theme is transformed into evaluation dimensions
2. **GitHub Search** - Repositories matching criteria are found
3. **Analysis** - Each repo's README, structure, and docs are analyzed
4. **Evaluation** - Claude evaluates each repo with confidence tracking
5. **Validation** - Results are validated for consistency
6. **Reflection** - Patterns are analyzed for insights
7. **Reports** - Multiple output formats are generated

## Example Output

```
🔍 Starting curation: Python CLI tools for developers

📋 Structuring intent...
   Created 4 evaluation dimensions:
   - usability (30%) with 4 indicators
   - documentation (25%) with 3 indicators
   - code_quality (25%) with 4 indicators
   - maintenance (20%) with 3 indicators

🔎 Searching GitHub...
   Found 10 candidate repositories

🧠 Evaluating repositories...
   Completed 10 evaluations

✅ Validating results...
   Intent: valid
   Results: valid

🤔 Analyzing patterns...
   Found 3 insights

📝 Generating reports...
   ✓ Markdown report: output/reports/curated_list_abc123.md
   ✓ Trace viewer: output/reports/trace_viewer_abc123.html

✨ Curation complete!
```

## Next Steps

- Read the [full usage guide](docs/USAGE.md)
- Try the [quickstart example](examples/quickstart.py)
- Explore [configuration options](config/curator.yaml)
- Review [implementation details](IMPLEMENTATION_SUMMARY.md)

## Troubleshooting

**API key issues?**
```bash
python -m curator setup
```

**Rate limiting?**
- GitHub API: 5000 requests/hour for authenticated users
- Adjust `rate_limit_buffer` in config if needed

**Low confidence evaluations?**
- Check `metacognitive_notes` in evaluation JSON
- Some repos just have limited documentation

## Learn More

📚 **Documentation**
- [USAGE.md](docs/USAGE.md) - Complete guide
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development
- [instructions.md](instructions.md) - Architecture

🎯 **IntentHub Principles**
- Transparency: Every score traces to evidence
- Metacognition: Explicit confidence tracking
- Validation: Multi-level consistency checks
- Reflection: Pattern-based learning

Happy curating! 🎉
