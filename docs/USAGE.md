# GitHub Curator Usage Guide

## Installation

```bash
# Clone the repository
git clone https://github.com/IntentHub/github-curator.git
cd github-curator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Setup

1. **Create environment variables file:**

```bash
cp .env.example .env
```

2. **Configure API keys in `.env`:**

```env
ANTHROPIC_API_KEY=your_anthropic_api_key
GITHUB_TOKEN=your_github_personal_access_token
```

3. **Verify setup:**

```bash
python -m curator setup
```

## Basic Usage

### Curate Repositories

```bash
# Basic curation
python -m curator curate "AI agents with tool use"

# With focus areas
python -m curator curate "machine learning visualization" \
  --focus "interactive dashboards" \
  --focus "real-time updates"

# With exclusions
python -m curator curate "Python web frameworks" \
  --exclude "tutorials only" \
  --exclude "unmaintained"

# Limit number of repositories
python -m curator curate "semantic search libraries" --limit 20

# Override minimum stars
python -m curator curate "prompt engineering tools" --min-stars 100

# Without HTML trace viewer
python -m curator curate "knowledge graphs" --no-trace
```

### View Results

```bash
# Show results from previous curation
python -m curator show <intent-id>

# Output files are in ./output/ directory:
# - output/summary.json - Quick summary
# - output/reports/*.md - Full markdown reports
# - output/reports/*.html - Interactive trace viewer
# - output/evaluations/*.json - Detailed evaluations
# - output/intent/*.json - Structured intent
# - output/validation/*.json - Validation reports
# - output/reflection/*.json - Reflection insights
```

### Validate Configuration

```bash
python -m curator validate-config
```

## Configuration

Edit [config/curator.yaml](../config/curator.yaml) to customize:

### Intent Structuring
```yaml
intent:
  default_weights:
    architectural_maturity: 0.3
    autonomy_level: 0.3
    safety: 0.2
    documentation: 0.2

  constraints:
    min_stars: 50
    max_age_months: 6
    requires_license: true
```

### GitHub Search
```yaml
github:
  search_limit: 100
  context_files:
    - README.md
    - ARCHITECTURE.md
    - docs/
    - examples/
```

### Evaluation Thresholds
```yaml
evaluation:
  confidence_threshold_high: 0.7
  confidence_threshold_low: 0.4
  min_indicators_found: 2
```

### Validation Rules
```yaml
validation:
  strict_mode: false
  fail_on_warnings: false
```

### Reflection
```yaml
reflection:
  min_evaluations_for_patterns: 10
  correlation_threshold: 0.7
```

### Output Formats
```yaml
output:
  formats:
    - markdown
    - json
    - html_trace
  trace_detail: full
```

## Example Curation Themes

### AI & Machine Learning
- "AI agents with autonomous decision-making"
- "LLM prompt engineering frameworks"
- "Semantic knowledge graph systems"
- "Machine learning model interpretability tools"

### Development Tools
- "Developer productivity CLI tools"
- "Code analysis and refactoring tools"
- "Testing frameworks with property-based testing"

### Architecture & Design
- "Microservices architecture examples"
- "Event-driven systems with CQRS"
- "Well-documented API design patterns"

### Data & Analytics
- "Real-time data visualization libraries"
- "Time series analysis frameworks"
- "Data pipeline orchestration tools"

## Understanding Output

### Markdown Reports

The markdown report includes:
- **Methodology**: Dimensions and weights used
- **Highly Recommended**: Repos with score ≥0.8 and confidence ≥0.7
- **Recommended**: Repos with score 0.6-0.8
- **Reflection Insights**: Patterns discovered during curation
- **Validation Report**: Quality assurance summary

### HTML Trace Viewer

Interactive visualization showing:
- All evaluated repositories sorted by relevance
- Click any repository to see dimension scores
- Evidence trail for each score
- Color-coded confidence levels

### JSON Artifacts

Machine-readable files for:
- Integration with other tools
- Historical analysis
- Custom reporting
- Audit trails

## Programmatic Usage

```python
from curator.core.intent_structuring import IntentStructurer
from curator.github.api_client import GitHubAPIClient
from curator.github.repo_analyzer import RepositoryAnalyzer
from curator.core.metacognitive_eval import MetacognitiveEvaluator

# Initialize
structurer = IntentStructurer()
github = GitHubAPIClient()
analyzer = RepositoryAnalyzer(github)
evaluator = MetacognitiveEvaluator()

# Structure intent
intent = structurer.structure_theme(
    theme="AI agents with tool use",
    focus_areas=["architecture", "safety"]
)

# Search repositories
repos = github.search_repositories(
    query="AI agents",
    min_stars=50
)

# Analyze and evaluate
for repo in repos:
    context = analyzer.analyze_repository(repo)
    summary = analyzer.get_evaluation_context_summary(context)
    evaluation = evaluator.evaluate_repository(context, intent, summary)
    print(f"{repo.full_name}: {evaluation.overall_relevance:.2f}")
```

## Troubleshooting

### Rate Limiting
- GitHub API has rate limits (5000 requests/hour for authenticated users)
- The client automatically sleeps when approaching limits
- Adjust `rate_limit_buffer` in config if needed

### Low Confidence Evaluations
- Repositories with limited documentation may have low confidence
- Check `metacognitive_notes` in evaluation JSON for details
- Consider adjusting `context_files` in config

### API Key Issues
```bash
# Verify environment variables
python -m curator setup

# Check .env file exists
ls -la .env
```

### Configuration Errors
```bash
# Validate configuration
python -m curator validate-config
```

## Best Practices

1. **Start Specific**: Use focused themes for better results
2. **Review Reflections**: Check insights to improve future curations
3. **Validate Results**: Review validation warnings
4. **Iterate**: Use reflection suggestions to refine criteria
5. **Document**: Save intent IDs for reproducibility

## Next Steps

- Read the [Implementation Specification](../instructions.md)
- Review [CLAUDE.md](../CLAUDE.md) for development guidance
- Explore example curations in [examples/](../examples/)
