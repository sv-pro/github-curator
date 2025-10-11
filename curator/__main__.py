"""Main CLI entry point for GitHub Curator."""

import os
from pathlib import Path
from typing import Optional

import click

# Load environment variables from .env file before other imports
from dotenv import load_dotenv

load_dotenv()

from curator.core.intent_structuring import IntentStructurer  # noqa: E402
from curator.core.metacognitive_eval import MetacognitiveEvaluator  # noqa: E402
from curator.core.reflection import Reflector  # noqa: E402
from curator.core.validation import Validator  # noqa: E402
from curator.github.adaptive_search import AdaptiveSearchStrategy, SearchConstraints  # noqa: E402
from curator.github.api_client import GitHubAPIClient  # noqa: E402
from curator.github.repo_analyzer import RepositoryAnalyzer  # noqa: E402
from curator.github.smart_fetcher import SmartRepoFetcher  # noqa: E402
from curator.outputs.report_generator import ReportGenerator  # noqa: E402


def parse_star_count(value: Optional[str]) -> Optional[int]:
    """Parse star count with k/m notation (e.g., '10k', '1m')."""
    if not value:
        return None

    value = value.lower().strip()

    # Handle numeric suffixes
    if value.endswith("k"):
        return int(float(value[:-1]) * 1000)
    elif value.endswith("m"):
        return int(float(value[:-1]) * 1000000)
    else:
        return int(value)


@click.group()
def cli():
    """GitHub Curator - Intelligent repository curation with metacognitive evaluation."""
    pass


@cli.command()
@click.argument("theme")
@click.option("--focus", "-f", multiple=True, help="Focus areas for curation")
@click.option("--exclude", "-e", multiple=True, help="Exclusion criteria")
@click.option("--config", "-c", default="config/curator.yaml", help="Configuration file path")
@click.option("--output", "-o", default="output", help="Output directory")
@click.option("--limit", "-l", type=int, help="Maximum repositories to evaluate")
@click.option(
    "--min-stars", help="Minimum stars - supports 1k, 10k, 1m notation (overrides config)"
)
@click.option(
    "--max-age-days", type=int, help="Maximum age in days since last push (overrides config)"
)
@click.option(
    "--use-git-clone", is_flag=True, help="Clone repos locally instead of using GitHub API (faster)"
)
@click.option("--trace/--no-trace", default=True, help="Generate HTML trace viewer")
@click.option(
    "--fetch-mode",
    type=click.Choice(["fast", "standard", "thorough", "exhaustive"], case_sensitive=False),
    default="standard",
    help="Analysis depth: fast (quick filter) | standard (balanced, default) | thorough (deep) | exhaustive (clone all)",
)
@click.option(
    "--disable-smart-fetch",
    is_flag=True,
    help="Disable smart fetching, analyze all repos fully (brute force)",
)
def curate(
    theme: str,
    focus: tuple,
    exclude: tuple,
    config: str,
    output: str,
    limit: Optional[int],
    min_stars: Optional[str],
    max_age_days: Optional[int],
    use_git_clone: bool,
    trace: bool,
    fetch_mode: str,
    disable_smart_fetch: bool,
):
    """Curate GitHub repositories based on a theme.

    THEME: Natural language description of what to curate (e.g., "AI agents with tool use")
    """
    click.echo(f"🔍 Starting curation: {theme}")
    click.echo("")

    try:
        # Initialize components
        structurer = IntentStructurer(config)
        github_client = GitHubAPIClient(config)
        analyzer = RepositoryAnalyzer(github_client, config, use_git_clone=use_git_clone)
        evaluator = MetacognitiveEvaluator(config)
        validator = Validator(config)
        reflector = Reflector(config)
        report_gen = ReportGenerator(output)

        # Step 1: Structure intent
        click.echo("📋 Structuring intent...")
        intent = structurer.structure_theme(
            theme=theme,
            focus_areas=list(focus) if focus else None,
            exclusions=list(exclude) if exclude else None,
        )
    except Exception as e:
        click.echo("\n❌ Error during initialization or intent structuring:", err=True)
        click.echo(f"   {type(e).__name__}: {e}", err=True)
        click.echo("\nTroubleshooting:", err=True)
        click.echo("  - Check your ANTHROPIC_API_KEY is valid", err=True)
        click.echo("  - Verify config/curator.yaml exists and is valid", err=True)
        click.echo("  - Run 'make setup' to verify configuration", err=True)
        raise click.Abort() from None

    click.echo(f"   Created {len(intent.dimensions)} evaluation dimensions:")
    for dim in intent.dimensions:
        click.echo(f"   - {dim.name} ({dim.weight*100:.0f}%) with {len(dim.indicators)} indicators")
    click.echo("")

    # Step 2: Validate intent
    click.echo("✅ Validating intent structure...")
    intent_validation = validator.validate_intent(intent)
    click.echo(f"   Status: {intent_validation.status}")
    if intent_validation.warnings:
        for warning in intent_validation.warnings[:3]:
            click.echo(f"   ⚠️  {warning.message}")
    click.echo("")

    # Step 3: Search repositories
    click.echo("🔎 Searching GitHub...")
    try:
        min_stars_val = parse_star_count(min_stars) or intent.constraints.min_stars
        # Convert days to months if specified
        max_age_months = (
            int(max_age_days / 30) if max_age_days else intent.constraints.max_age_months
        )

        # Use adaptive search strategy
        adaptive_search = AdaptiveSearchStrategy(config)
        constraints = SearchConstraints(
            min_stars=min_stars_val,
            max_age_months=max_age_months,
            requires_license=intent.constraints.requires_license,
        )

        repos = adaptive_search.adaptive_search(
            theme=theme, github_client=github_client, initial_constraints=constraints, limit=limit
        )

        click.echo(f"   Selected {len(repos)} candidate repositories for evaluation")
        click.echo("")
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__

        # Detect specific error types for better troubleshooting
        if "credit balance" in error_msg.lower() or "anthropic api" in error_msg.lower():
            click.echo("\n❌ Anthropic API Error:", err=True)
            click.echo(f"   {error_type}: {e}", err=True)
            click.echo("\nTroubleshooting:", err=True)
            click.echo("  - Check your ANTHROPIC_API_KEY is valid", err=True)
            click.echo("  - Verify your Anthropic account has sufficient credits", err=True)
            click.echo("  - Visit https://console.anthropic.com/settings/billing", err=True)
        elif "github" in error_msg.lower() or "rate limit" in error_msg.lower():
            click.echo("\n❌ GitHub API Error:", err=True)
            click.echo(f"   {error_type}: {e}", err=True)
            click.echo("\nTroubleshooting:", err=True)
            click.echo("  - Check your GITHUB_TOKEN is valid", err=True)
            click.echo("  - Verify you haven't exceeded GitHub API rate limits", err=True)
            click.echo("  - Check your internet connection", err=True)
        else:
            click.echo("\n❌ Error during search:", err=True)
            click.echo(f"   {error_type}: {e}", err=True)
        raise click.Abort() from None

    if not repos:
        click.echo("⚠️  No repositories found matching criteria", err=True)
        raise click.Abort()

    # Step 4: Analyze and evaluate
    click.echo("🧠 Evaluating repositories...")

    # Initialize smart fetcher or use brute force
    use_smart_fetch = not disable_smart_fetch
    if use_smart_fetch:
        click.echo(f"   Using smart fetching mode: {fetch_mode}")
        smart_fetcher = SmartRepoFetcher(config, intent, github_client, analyzer, evaluator)
    else:
        click.echo("   Using brute force evaluation (smart fetch disabled)")
        smart_fetcher = None

    click.echo("")
    evaluations = []
    skipped_count = 0

    try:
        for idx, repo in enumerate(repos, 1):
            click.echo(f"[{idx}/{len(repos)}] {repo.full_name}")

            if use_smart_fetch and smart_fetcher:
                # Use smart fetcher
                evaluation = smart_fetcher.analyze(repo, thoroughness=fetch_mode)

                if evaluation is None:
                    # Repository was skipped
                    click.echo("  ⊘ Skipped (filtered by smart fetch)")
                    skipped_count += 1
                    click.echo("")
                    continue
                else:
                    evaluations.append(evaluation)
                    click.echo(
                        f"  ✓ Score: {evaluation.overall_relevance:.2f}, Confidence: {evaluation.confidence:.2f}"
                    )
                    click.echo("")
            else:
                # Brute force: evaluate everything
                click.echo("  → Fetching README...")
                context = analyzer.analyze_repository(repo)

                click.echo("  → Generating context summary...")
                context_summary = analyzer.get_evaluation_context_summary(context)

                # Evaluate
                click.echo("  → Evaluating with Claude...")
                evaluation = evaluator.evaluate_repository(context, intent, context_summary)
                evaluations.append(evaluation)

                click.echo(
                    f"  ✓ Score: {evaluation.overall_relevance:.2f}, Confidence: {evaluation.confidence:.2f}"
                )
                click.echo("")
    except KeyboardInterrupt:
        click.echo("\n\n⚠️  Evaluation interrupted by user", err=True)
        if evaluations:
            click.echo(f"   Processed {len(evaluations)} repositories before interruption")
            click.echo("   Continuing with partial results...")
        else:
            click.echo("   No evaluations completed", err=True)
            raise click.Abort() from None
    except Exception as e:
        click.echo("\n❌ Error during evaluation:", err=True)
        click.echo(f"   {type(e).__name__}: {e}", err=True)
        if evaluations:
            click.echo(f"   Processed {len(evaluations)} repositories before error")
            click.echo("   Continuing with partial results...")
        else:
            raise click.Abort() from None

    click.echo(f"   Completed {len(evaluations)} evaluations")
    click.echo("")

    # Step 5: Validate results
    click.echo("✅ Validating results...")
    validation_report = validator.validate_all(intent, evaluations)
    click.echo(f"   Intent: {validation_report.intent_validation.status}")
    click.echo(f"   Results: {validation_report.results_validation.status}")

    # Show score distribution
    score_dist = validation_report.results_validation.score_distribution
    click.echo("   Score distribution:")
    for range_key, count in score_dist.items():
        if count > 0:
            click.echo(f"     {range_key}: {count} repos")
    click.echo("")

    # Step 6: Reflect on patterns
    click.echo("🤔 Analyzing patterns...")
    reflection = reflector.reflect(evaluations, intent)
    click.echo(f"   Found {len(reflection.insights)} insights")
    if reflection.insights:
        for insight in reflection.insights[:3]:
            click.echo(f"   - {insight.description}")
    click.echo("")

    # Step 7: Generate reports
    click.echo("📝 Generating reports...")

    # Save JSON artifacts
    report_gen.save_json_artifacts(intent, evaluations, validation_report, reflection)
    click.echo(f"   ✓ JSON artifacts saved to {output}/")

    # Generate summary
    summary_path = report_gen.generate_summary_json(
        intent, evaluations, validation_report, reflection
    )
    click.echo(f"   ✓ Summary: {summary_path}")

    # Generate markdown report
    md_path = report_gen.generate_markdown_report(
        intent, evaluations, validation_report, reflection
    )
    click.echo(f"   ✓ Markdown report: {md_path}")

    # Generate trace viewer
    if trace:
        html_path = report_gen.generate_html_trace_viewer(intent, evaluations)
        click.echo(f"   ✓ Trace viewer: {html_path}")

    click.echo("")

    # Show smart fetch savings
    if use_smart_fetch and smart_fetcher:
        savings = smart_fetcher.get_savings_summary()
        if savings["skipped_count"] > 0:
            click.echo("💰 Smart Fetch Savings:")
            click.echo(
                f"   Repos analyzed: {savings['analyzed_count']} | "
                f"Skipped: {savings['skipped_count']} ({savings['skip_rate']:.0%})"
            )
            if savings["cost_saved"] > 0:
                click.echo(f"   Estimated cost saved: ${savings['cost_saved']:.2f}")
            click.echo("")

    click.echo("✨ Curation complete!")

    # Show top results
    top_repos = sorted(
        evaluations, key=lambda e: (e.overall_relevance, e.confidence), reverse=True
    )[:5]
    if top_repos:
        click.echo("")
        click.echo("🌟 Top Results:")
        for i, eval in enumerate(top_repos, 1):
            click.echo(
                f"   {i}. {eval.repo} (score: {eval.overall_relevance:.2f}, conf: {eval.confidence:.2f})"
            )


@cli.command()
@click.argument("topics", nargs=-1)
@click.option("--repo", "-r", multiple=True, help="Specific repo(s) to add (owner/repo or URL)")
@click.option(
    "--limit", "-l", type=int, default=100, help="Maximum number of repos per topic to collect"
)
@click.option("--min-stars", type=int, default=50, help="Minimum stars")
@click.option("--knowledge-base", default=".curator/knowledge", help="Knowledge base directory")
@click.option("--language", help="Filter by programming language")
@click.option("--refresh", is_flag=True, help="Refresh existing repos (default: skip duplicates)")
@click.option(
    "--use-git-clone", is_flag=True, help="Clone repos locally instead of using GitHub API (faster)"
)
@click.option("--config", "-c", default="config/curator.yaml", help="Configuration file path")
def collect(
    topics: tuple[str, ...],
    repo: tuple[str, ...],
    limit: int,
    min_stars: int,
    knowledge_base: str,
    language: Optional[str],
    refresh: bool,
    use_git_clone: bool,
    config: str,
):
    """Collect repositories and add to knowledge base.

    TOPICS: One or more GitHub topics to search for (e.g., "async", "web-framework")

    Use --repo to add specific repositories instead of searching by topic.
    Supports both formats: owner/repo or https://github.com/owner/repo

    By default, skips repositories already in the knowledge base.
    Use --refresh to update existing repos with latest data.

    Examples:

        # Single topic
        curator collect async --language python

        # Multiple topics
        curator collect async asyncio concurrency --language python

        # Specific repositories
        curator collect --repo fastapi/fastapi --repo django/django

        # URL format
        curator collect --repo https://github.com/pallets/flask

        # Refresh existing
        curator collect async --refresh

    This builds a corpus of repositories in the knowledge base that can be used
    by the 'mark' command for better topic inference.
    """
    from curator.commands import collect_repositories

    # Validate inputs
    if not topics and not repo:
        click.echo("❌ Either TOPICS or --repo must be provided", err=True)
        raise click.Abort()

    if topics and repo:
        click.echo("⚠️  Both topics and --repo provided, will collect both")
        click.echo("")

    if topics:
        if len(topics) == 1:
            click.echo(f"📚 Collecting repositories with topic: {topics[0]}")
        else:
            click.echo(f"📚 Collecting repositories with {len(topics)} topics:")
            for topic in topics:
                click.echo(f"   • {topic}")
    else:
        click.echo(f"📚 Collecting {len(repo)} specific repository/ies")
    click.echo("")

    try:
        result = collect_repositories(
            topics=list(topics) if topics else None,
            specific_repos=list(repo) if repo else None,
            limit=limit,
            min_stars=min_stars,
            language=language,
            knowledge_base_path=knowledge_base,
            refresh_existing=refresh,
            use_git_clone=use_git_clone,
            config_path=config,
        )

        # Display summary
        if result.get("errors"):
            click.echo(f"\n⚠️  Warnings: {len(result['errors'])} repositories failed", err=True)

    except Exception as e:
        error_msg = str(e)
        if "github" in error_msg.lower() or "rate limit" in error_msg.lower():
            click.echo("\n❌ GitHub API Error:", err=True)
            click.echo(f"   {type(e).__name__}: {e}", err=True)
            click.echo("  - Check GITHUB_TOKEN is valid and has sufficient rate limit", err=True)
            click.echo("  - GitHub rate limit: 5000 req/hour (authenticated)", err=True)
        else:
            click.echo(f"\n❌ Error collecting repositories: {e}", err=True)
        raise click.Abort() from None


def _print_topic_suggestions(context, suggestions, compare):
    """Print topic suggestions in text format."""
    click.echo(f"📊 Topic Analysis: {context.full_name}")
    click.echo("")

    # Show current topics if compare mode
    if compare and context.metadata.topics:
        click.echo(f"Current Topics ({len(context.metadata.topics)}):")
        click.echo(f"  {', '.join(context.metadata.topics)}")
        click.echo("")

    # Group suggestions by confidence
    high_conf = [s for s in suggestions if s.confidence >= 0.8]
    med_conf = [s for s in suggestions if 0.6 <= s.confidence < 0.8]
    low_conf = [s for s in suggestions if 0.5 <= s.confidence < 0.6]

    click.echo(f"Suggested Topics ({len(suggestions)}):")
    click.echo("")

    if high_conf:
        click.echo("High Confidence (≥0.8):")
        for s in high_conf:
            status = "✓" if s.already_assigned else "✨"
            sources = ", ".join(s.sources)
            click.echo(f"  {status} {s.topic} ({s.confidence:.2f})")
            click.echo(f"     {s.reasoning}")
            click.echo(f"     Sources: {sources}")
            click.echo("")

    if med_conf:
        click.echo("Medium Confidence (0.6-0.8):")
        for s in med_conf:
            status = "✓" if s.already_assigned else "💡"
            sources = ", ".join(s.sources)
            click.echo(f"  {status} {s.topic} ({s.confidence:.2f})")
            click.echo(f"     {s.reasoning}")
            click.echo("")

    if low_conf:
        click.echo("Lower Confidence (0.5-0.6):")
        for s in low_conf:
            status = "✓" if s.already_assigned else "🤔"
            click.echo(f"  {status} {s.topic} ({s.confidence:.2f}) - {s.reasoning}")


@cli.command()
@click.argument("repo")  # owner/repo format
@click.option("--compare", is_flag=True, help="Show current topics vs AI suggestions")
@click.option("--from-curation", help="Load knowledge from curation results directory")
@click.option("--knowledge-base", default=".curator/knowledge", help="Knowledge base directory")
@click.option("--min-confidence", type=float, default=0.5, help="Minimum confidence threshold")
@click.option("--output", "-o", help="Output file path (JSON format)")
@click.option(
    "--format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.option("--config", "-c", default="config/curator.yaml", help="Configuration file path")
@click.option(
    "--use-git-clone", is_flag=True, help="Clone repo locally instead of using GitHub API"
)
def mark(
    repo: str,
    compare: bool,
    from_curation: Optional[str],
    knowledge_base: str,
    min_confidence: float,
    output: Optional[str],
    format: str,
    config: str,
    use_git_clone: bool,
):
    """Analyze repository and suggest relevant topics.

    REPO: Repository in owner/repo format (e.g., fastapi/fastapi)

    By default, operates in BLIND MODE - analyzes the repository WITHOUT
    looking at existing topics. Use --compare to see current vs suggested topics.

    Examples:

        # Blind mode analysis (default)
        curator mark fastapi/fastapi

        # Compare with existing topics
        curator mark fastapi/fastapi --compare

        # Load knowledge from curation results
        curator mark fastapi/fastapi --from-curation output/

        # Save results to file
        curator mark fastapi/fastapi --output results.json --format json
    """
    import json
    from datetime import datetime

    import yaml
    from anthropic import Anthropic

    from curator.core.topic_inference import TopicInferenceEngine
    from curator.knowledge import KnowledgeBase

    click.echo(f"🏷️  Analyzing topics for: {repo}")
    click.echo("")

    try:
        # Load config
        with open(config) as f:
            cfg = yaml.safe_load(f)

        # Initialize components
        github_client = GitHubAPIClient(config)
        analyzer = RepositoryAnalyzer(github_client, config, use_git_clone=use_git_clone)

        # Get LLM provider configuration
        llm_config = cfg.get("llm", {})
        provider_name = llm_config.get("provider", "anthropic")
        use_langchain = llm_config.get("use_langchain", True)
        models = llm_config.get("models", {})
        model = models.get(provider_name, "claude-sonnet-4-5-20250929")

        # For backward compatibility, also support direct Anthropic client
        if provider_name == "anthropic" and not use_langchain:
            anthropic_client = Anthropic()
        else:
            # Use the new factory (but we need to adapt it for the inference engine)
            # For now, create Anthropic client directly since TopicInferenceEngine expects it
            anthropic_client = Anthropic()

        # Initialize knowledge base
        kb = KnowledgeBase(base_path=knowledge_base)

        # Load from curation if specified
        if from_curation:
            click.echo(f"📚 Loading knowledge from: {from_curation}")
            kb.load_from_curation(Path(from_curation))
            kb.learn_patterns()
            kb.save()

        kb_stats = kb.get_stats()
        click.echo(
            f"   Knowledge base: {kb_stats['total_repositories']} repos, {kb_stats['total_patterns']} patterns"
        )
        click.echo("")

        # Fetch repository
        click.echo("📊 Fetching repository data...")
        from curator.github.api_client import SearchResult

        gh_repo = github_client.get_repository(repo)
        search_result = SearchResult(
            name=gh_repo.name,
            owner=gh_repo.owner.login,
            full_name=gh_repo.full_name,
            description=gh_repo.description or "",
            url=gh_repo.html_url,
            stars=gh_repo.stargazers_count,
            last_updated=gh_repo.pushed_at,
            language=gh_repo.language or "Unknown",
            license_name=gh_repo.license.name if gh_repo.license else None,
            topics=list(gh_repo.get_topics()),
        )

        # Analyze repository
        click.echo("🔍 Analyzing repository content...")
        context = analyzer.analyze_repository(search_result)

        # Extract features
        features = analyzer.extract_key_features(context)

        # Initialize inference engine
        inference = TopicInferenceEngine(kb, anthropic_client, model)

        # Infer topics (blind mode by default)
        click.echo("🤖 Inferring topics with AI...")
        suggestions = inference.infer_topics(context, features, blind_mode=not compare)

        # Filter by confidence
        suggestions = [s for s in suggestions if s.confidence >= min_confidence]

        click.echo("")

        # Output results
        if format == "json":
            result = {
                "repository": repo,
                "analyzed_at": datetime.utcnow().isoformat(),
                "current_topics": list(context.metadata.topics) if compare else None,
                "suggestions": [s.to_dict() for s in suggestions],
                "knowledge_base": kb_stats,
            }

            if output:
                Path(output).parent.mkdir(parents=True, exist_ok=True)
                with open(output, "w") as f:
                    json.dump(result, f, indent=2)
                click.echo(f"✓ Results saved to: {output}")
            else:
                click.echo(json.dumps(result, indent=2))

        else:  # text format
            _print_topic_suggestions(context, suggestions, compare)

            if output:
                # Save as JSON even in text mode if output specified
                result = {
                    "repository": repo,
                    "analyzed_at": datetime.utcnow().isoformat(),
                    "current_topics": list(context.metadata.topics) if compare else None,
                    "suggestions": [s.to_dict() for s in suggestions],
                }
                Path(output).parent.mkdir(parents=True, exist_ok=True)
                with open(output, "w") as f:
                    json.dump(result, f, indent=2)
                click.echo(f"\n✓ Results also saved to: {output}")

    except Exception as e:
        click.echo(f"\n❌ Error: {type(e).__name__}: {e}", err=True)
        raise click.Abort() from None


@cli.command()
@click.argument("intent_id")
@click.option("--output", "-o", default="output", help="Output directory")
def show(intent_id: str, output: str):
    """Show results from a previous curation by intent ID."""
    import json

    output_path = Path(output)

    # Load intent
    intent_file = output_path / "intent" / f"{intent_id}.json"
    if not intent_file.exists():
        click.echo(f"❌ Intent {intent_id} not found", err=True)
        return

    with open(intent_file) as f:
        intent_data = json.load(f)

    click.echo(f"Theme: {intent_data['theme']}")
    click.echo(f"Dimensions: {len(intent_data['dimensions'])}")

    # Load summary if available
    summary_file = output_path / "summary.json"
    if summary_file.exists():
        with open(summary_file) as f:
            summary = json.load(f)

        click.echo(f"\nTotal evaluated: {summary['statistics']['total_evaluated']}")
        click.echo(f"Highly relevant: {summary['statistics']['highly_relevant']}")

        click.echo("\nTop repositories:")
        for i, repo in enumerate(summary["top_repositories"][:10], 1):
            click.echo(f"  {i}. {repo['repo']} ({repo['score']:.2f})")


@cli.command()
def validate_config():
    """Validate configuration files."""
    import yaml

    config_path = Path("config/curator.yaml")

    if not config_path.exists():
        click.echo("❌ config/curator.yaml not found", err=True)
        return

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)

        click.echo("✅ Configuration is valid")
        click.echo(f"   Intent dimensions: {len(config['intent']['default_weights'])}")
        click.echo(f"   GitHub search limit: {config['github']['search_limit']}")
        click.echo(f"   Output formats: {', '.join(config['output']['formats'])}")

    except Exception as e:
        click.echo(f"❌ Configuration error: {e}", err=True)


@cli.command()
@click.argument("repo_url")
@click.option(
    "--base-path", help="Base directory for tracked repos (default: ~/.github-curator/tracked)"
)
def track(repo_url: str, base_path: Optional[str]):
    """Start tracking a repository for curation history.

    REPO_URL: GitHub repository URL (e.g., https://github.com/owner/repo)

    This clones the repository locally and initializes CURATION.md and REVIEW.md
    files for tracking evaluation history over time.

    Examples:

        curator track https://github.com/fastapi/fastapi
        curator track https://github.com/pallets/flask --base-path ~/my-curated-repos
    """
    from curator.tracking import RepoTracker

    try:
        tracker = RepoTracker(Path(base_path) if base_path else None)

        click.echo(f"📦 Tracking repository: {repo_url}")
        click.echo("")

        info = tracker.track(repo_url)

        click.echo("✅ Successfully initialized tracking!")
        click.echo(f"   Organization: {info.org}")
        click.echo(f"   Repository: {info.repo}")
        click.echo(f"   Local path: {info.local_path}")
        click.echo("   Branch: curation")
        click.echo("")
        click.echo("📝 Files created:")
        click.echo("   - CURATION.md (evaluation history)")
        click.echo("   - REVIEW.md (latest review)")
        click.echo("")
        click.echo("Next steps:")
        click.echo(f'   curator curate-tracked {info.org}/{info.repo} --theme "Your theme"')

    except ValueError as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort() from None
    except Exception as e:
        click.echo(f"❌ Unexpected error: {type(e).__name__}: {e}", err=True)
        raise click.Abort() from None


@cli.command()
@click.option("--base-path", help="Base directory for tracked repos")
def list_tracked(base_path: Optional[str]):
    """List all tracked repositories."""
    from curator.tracking import RepoTracker

    tracker = RepoTracker(Path(base_path) if base_path else None)
    tracked = tracker.list_tracked()

    if not tracked:
        click.echo("📭 No tracked repositories found")
        click.echo(f"   Looking in: {tracker.base_path}")
        click.echo("")
        click.echo("To start tracking a repository:")
        click.echo("   curator track https://github.com/owner/repo")
        return

    click.echo(f"📚 Tracked Repositories ({len(tracked)})")
    click.echo("")

    for info in sorted(tracked, key=lambda x: x.last_updated, reverse=True):
        click.echo(f"• {info.org}/{info.repo}")
        click.echo(f"  Path: {info.local_path}")
        click.echo(f"  Curations: {info.curation_count}")
        click.echo(f"  Last updated: {info.last_updated.strftime('%Y-%m-%d %H:%M UTC')}")
        click.echo("")


@cli.command()
@click.argument("repo")  # org/repo format
@click.argument("theme")
@click.option("--base-path", help="Base directory for tracked repos")
@click.option("--config", "-c", default="config/curator.yaml", help="Configuration file path")
@click.option("--use-git-clone", is_flag=True, help="Clone repo locally for analysis")
def curate_tracked(
    repo: str, theme: str, base_path: Optional[str], config: str, use_git_clone: bool
):
    """Curate a tracked repository and update its history.

    REPO: Repository in org/repo format (e.g., fastapi/fastapi)
    THEME: Curation theme (e.g., "Web frameworks for async Python")

    This evaluates the repository, appends to CURATION.md, updates REVIEW.md,
    and creates a git commit + tag for traceability.

    Examples:

        curator curate-tracked fastapi/fastapi "Modern async web frameworks"
        curator curate-tracked pallets/flask "Beginner-friendly web frameworks"
    """
    from curator.core.intent_structuring import IntentStructurer
    from curator.core.metacognitive_eval import MetacognitiveEvaluator
    from curator.github.api_client import GitHubAPIClient, SearchResult
    from curator.github.repo_analyzer import RepositoryAnalyzer
    from curator.tracking import CurationFileManager, RepoTracker, ReviewGenerator

    try:
        # Initialize tracker
        tracker = RepoTracker(Path(base_path) if base_path else None)
        org, repo_name = repo.split("/")

        if not tracker.is_tracked(org, repo_name):
            click.echo(f"❌ Repository {repo} is not tracked", err=True)
            click.echo(f"   Run: curator track https://github.com/{repo}", err=True)
            raise click.Abort()

        click.echo(f"🎯 Curating tracked repository: {repo}")
        click.echo(f"   Theme: {theme}")
        click.echo("")

        # Update from upstream
        click.echo("🔄 Checking for updates from upstream...")
        has_updates = tracker.update_from_upstream(org, repo_name)
        if has_updates:
            click.echo("   ✓ Pulled latest changes")
        else:
            click.echo("   ✓ Already up to date")
        click.echo("")

        # Initialize curation components
        click.echo("🧠 Initializing evaluation...")
        structurer = IntentStructurer(config)
        github_client = GitHubAPIClient(config)
        analyzer = RepositoryAnalyzer(github_client, config, use_git_clone=use_git_clone)
        evaluator = MetacognitiveEvaluator(config)

        # Structure intent
        click.echo("📋 Structuring intent...")
        intent = structurer.structure_theme(theme)
        click.echo(f"   Created {len(intent.dimensions)} evaluation dimensions")
        click.echo("")

        # Get repository info
        click.echo("📊 Fetching repository data...")
        gh_repo = github_client.get_repository(repo)
        search_result = SearchResult(
            name=gh_repo.name,
            owner=gh_repo.owner.login,
            full_name=gh_repo.full_name,
            description=gh_repo.description or "",
            url=gh_repo.html_url,
            stars=gh_repo.stargazers_count,
            last_updated=gh_repo.pushed_at,
            language=gh_repo.language or "Unknown",
            license_name=gh_repo.license.name if gh_repo.license else None,
            topics=list(gh_repo.get_topics()),
        )

        # Analyze repository
        click.echo("🔍 Analyzing repository content...")
        context = analyzer.analyze_repository(search_result)
        context_summary = analyzer.get_evaluation_context_summary(context)

        # Evaluate
        click.echo("🤖 Evaluating with Claude...")
        evaluation = evaluator.evaluate_repository(context, intent, context_summary)

        click.echo(f"   ✓ Score: {evaluation.overall_relevance:.2f}")
        click.echo(f"   ✓ Confidence: {evaluation.confidence:.2f}")
        click.echo("")

        # Format CURATION.md entry
        click.echo("📝 Generating curation files...")

        # Get current commit hash of the evaluated repo
        repo_path = tracker.get_repo_path(org, repo_name)
        import subprocess

        result = subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        repo_commit = result.stdout.strip()

        # Prepare dimension data
        dimensions = {}
        evidence_items = []

        for dim_score in evaluation.dimension_scores:
            dimensions[dim_score.dimension] = {
                "score": dim_score.score,
                "confidence": dim_score.confidence,
                "reasoning": dim_score.reasoning,
            }
            # Collect evidence from indicators
            for indicator in dim_score.found_indicators[:3]:  # Top 3 per dimension
                evidence_items.append(f"{indicator.indicator}: {indicator.evidence}")

        # Generate CURATION.md entry
        curation_content = CurationFileManager.format_entry(
            theme=theme,
            overall_score=evaluation.overall_relevance,
            confidence=evaluation.confidence,
            dimensions=dimensions,
            evidence=evidence_items[:10],  # Top 10 total
            repo_commit=repo_commit,
        )

        # Generate REVIEW.md content with LLM
        review_generator = ReviewGenerator()
        review_content = review_generator.generate_review(
            org=org,
            repo=repo_name,
            theme=theme,
            overall_score=evaluation.overall_relevance,
            confidence=evaluation.confidence,
            dimensions=dimensions,
            evidence=evidence_items[:10],
            repo_description=search_result.description,
            readme_excerpt=context.readme_content[:1000] if context.readme_content else None,
        )

        # Add curation to tracked repo
        tag = tracker.add_curation(org, repo_name, curation_content, review_content, theme)

        click.echo("   ✓ Updated CURATION.md")
        click.echo("   ✓ Updated REVIEW.md")
        click.echo(f"   ✓ Created commit and tag: {tag}")
        click.echo("")

        click.echo("✨ Curation complete!")
        click.echo("")
        click.echo("View history:")
        click.echo(f"   cd {repo_path}")
        click.echo("   git log --oneline")
        click.echo("   cat .curator/CURATION.md")
        click.echo("   cat .curator/REVIEW.md")

    except ValueError as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort() from None
    except Exception as e:
        click.echo(f"❌ Unexpected error: {type(e).__name__}: {e}", err=True)
        import traceback

        traceback.print_exc()
        raise click.Abort() from None


@cli.command()
@click.argument("repo")  # org/repo format
@click.argument("theme")
@click.option("--base-path", help="Base directory for tracked repos")
@click.option("--config", "-c", default="config/curator.yaml", help="Configuration file path")
@click.option("--use-git-clone", is_flag=True, help="Clone repo locally for analysis")
def review(repo: str, theme: str, base_path: Optional[str], config: str, use_git_clone: bool):
    """Quick review update for tracked repository.

    REPO: Repository in org/repo format (e.g., fastapi/fastapi)
    THEME: Review theme (e.g., "Modern Python web frameworks")

    This is a lighter version of curate-tracked:
    - Pulls all branches from upstream
    - Evaluates the main branch
    - Updates REVIEW.md (does NOT append to CURATION.md)
    - Creates git commit + tag on curation branch

    Use this for quick review updates without adding to full curation history.

    Examples:

        curator review fastapi/fastapi "Modern async web frameworks"
        curator review pallets/flask "Python web frameworks 2025"
    """
    from curator.core.intent_structuring import IntentStructurer
    from curator.core.metacognitive_eval import MetacognitiveEvaluator
    from curator.github.api_client import GitHubAPIClient, SearchResult
    from curator.github.repo_analyzer import RepositoryAnalyzer
    from curator.tracking import RepoTracker, ReviewGenerator

    try:
        # Initialize tracker
        tracker = RepoTracker(Path(base_path) if base_path else None)
        org, repo_name = repo.split("/")

        if not tracker.is_tracked(org, repo_name):
            click.echo(f"❌ Repository {repo} is not tracked", err=True)
            click.echo(f"   Run: curator track https://github.com/{repo}", err=True)
            raise click.Abort()

        click.echo(f"🔄 Reviewing tracked repository: {repo}")
        click.echo(f"   Theme: {theme}")
        click.echo("")

        # Sync all branches
        click.echo("📥 Syncing all branches from upstream...")
        updates = tracker.sync_all_branches(org, repo_name)

        updated_branches = [b for b, updated in updates.items() if updated]
        if updated_branches:
            click.echo(f"   ✓ Updated branches: {', '.join(updated_branches)}")
        else:
            click.echo("   ✓ All branches up to date")
        click.echo("")

        # Initialize evaluation components
        click.echo("🧠 Initializing evaluation...")
        structurer = IntentStructurer(config)
        github_client = GitHubAPIClient(config)
        analyzer = RepositoryAnalyzer(github_client, config, use_git_clone=use_git_clone)
        evaluator = MetacognitiveEvaluator(config)

        # Structure intent
        click.echo("📋 Structuring intent...")
        intent = structurer.structure_theme(theme)
        click.echo(f"   Created {len(intent.dimensions)} evaluation dimensions")
        click.echo("")

        # Get repository info
        click.echo("📊 Fetching repository data...")
        gh_repo = github_client.get_repository(repo)
        search_result = SearchResult(
            name=gh_repo.name,
            owner=gh_repo.owner.login,
            full_name=gh_repo.full_name,
            description=gh_repo.description or "",
            url=gh_repo.html_url,
            stars=gh_repo.stargazers_count,
            last_updated=gh_repo.pushed_at,
            language=gh_repo.language or "Unknown",
            license_name=gh_repo.license.name if gh_repo.license else None,
            topics=list(gh_repo.get_topics()),
        )

        # Analyze repository
        click.echo("🔍 Analyzing repository content...")
        context = analyzer.analyze_repository(search_result)
        context_summary = analyzer.get_evaluation_context_summary(context)

        # Evaluate
        click.echo("🤖 Evaluating with Claude...")
        evaluation = evaluator.evaluate_repository(context, intent, context_summary)

        click.echo(f"   ✓ Score: {evaluation.overall_relevance:.2f}")
        click.echo(f"   ✓ Confidence: {evaluation.confidence:.2f}")
        click.echo("")

        # Generate review content
        click.echo("📝 Generating review...")

        # Prepare dimension data
        dimensions = {}
        evidence_items = []

        for dim_score in evaluation.dimension_scores:
            dimensions[dim_score.dimension] = {
                "score": dim_score.score,
                "confidence": dim_score.confidence,
                "reasoning": dim_score.reasoning,
            }
            # Collect evidence from indicators
            for indicator in dim_score.found_indicators[:3]:  # Top 3 per dimension
                evidence_items.append(f"{indicator.indicator}: {indicator.evidence}")

        # Generate rich REVIEW.md with LLM
        review_generator = ReviewGenerator()
        review_content = review_generator.generate_review(
            org=org,
            repo=repo_name,
            theme=theme,
            overall_score=evaluation.overall_relevance,
            confidence=evaluation.confidence,
            dimensions=dimensions,
            evidence=evidence_items[:10],
            repo_description=search_result.description,
            readme_excerpt=context.readme_content[:1000] if context.readme_content else None,
        )

        # Update review (not full curation)
        tag = tracker.update_review(org, repo_name, review_content, theme)

        click.echo("   ✓ Updated .curator/REVIEW.md")
        click.echo(f"   ✓ Created commit and tag: {tag}")
        click.echo("")

        click.echo("✨ Review complete!")
        click.echo("")
        click.echo("View review:")
        repo_path = tracker.get_repo_path(org, repo_name)
        click.echo(f"   cat {repo_path}/.curator/REVIEW.md")
        click.echo("")
        click.echo("Note: CURATION.md history was not modified.")
        click.echo("      Use 'curator curate-tracked' to add full curation entry.")

    except ValueError as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort() from None
    except Exception as e:
        click.echo(f"❌ Unexpected error: {type(e).__name__}: {e}", err=True)
        import traceback

        traceback.print_exc()
        raise click.Abort() from None


@cli.command()
def setup():
    """Check setup and environment variables."""
    issues = []

    # Check API keys
    if not os.getenv("ANTHROPIC_API_KEY"):
        issues.append("❌ ANTHROPIC_API_KEY not set")
    else:
        click.echo("✅ ANTHROPIC_API_KEY is set")

    if not os.getenv("GITHUB_TOKEN"):
        issues.append("❌ GITHUB_TOKEN not set")
    else:
        click.echo("✅ GITHUB_TOKEN is set")

    # Check config
    if not Path("config/curator.yaml").exists():
        issues.append("❌ config/curator.yaml not found")
    else:
        click.echo("✅ config/curator.yaml exists")

    # Check directories
    for dir_name in ["data/criteria", "data/evaluations", "data/reflections"]:
        if not Path(dir_name).exists():
            issues.append(f"❌ {dir_name} directory missing")

    if issues:
        click.echo("\nIssues found:")
        for issue in issues:
            click.echo(f"  {issue}")
        click.echo("\nSetup incomplete. Please resolve issues above.")
    else:
        click.echo("\n✅ Setup complete! Ready to curate.")


if __name__ == "__main__":
    cli()
