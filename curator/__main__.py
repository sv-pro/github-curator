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
from curator.github.api_client import GitHubAPIClient  # noqa: E402
from curator.github.repo_analyzer import RepositoryAnalyzer  # noqa: E402
from curator.outputs.report_generator import ReportGenerator  # noqa: E402


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
@click.option("--min-stars", type=int, help="Minimum stars (overrides config)")
@click.option("--trace/--no-trace", default=True, help="Generate HTML trace viewer")
def curate(
    theme: str,
    focus: tuple,
    exclude: tuple,
    config: str,
    output: str,
    limit: Optional[int],
    min_stars: Optional[int],
    trace: bool,
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
        analyzer = RepositoryAnalyzer(github_client, config)
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
        min_stars_val = min_stars or intent.constraints.min_stars
        repos = github_client.search_repositories(
            query=theme,
            min_stars=min_stars_val,
            max_age_months=intent.constraints.max_age_months,
            requires_license=intent.constraints.requires_license,
            limit=limit,
        )
        click.echo(f"   Found {len(repos)} candidate repositories")
        click.echo("")
    except Exception as e:
        click.echo("\n❌ Error searching GitHub:", err=True)
        click.echo(f"   {type(e).__name__}: {e}", err=True)
        click.echo("\nTroubleshooting:", err=True)
        click.echo("  - Check your GITHUB_TOKEN is valid", err=True)
        click.echo("  - Verify you haven't exceeded GitHub API rate limits", err=True)
        click.echo("  - Check your internet connection", err=True)
        raise click.Abort() from None

    if not repos:
        click.echo("⚠️  No repositories found matching criteria", err=True)
        raise click.Abort()

    # Step 4: Analyze and evaluate
    click.echo("🧠 Evaluating repositories...")
    evaluations = []

    try:
        with click.progressbar(repos, label="Analyzing") as bar:
            for repo in bar:
                # Gather context
                context = analyzer.analyze_repository(repo)
                context_summary = analyzer.get_evaluation_context_summary(context)

                # Evaluate
                evaluation = evaluator.evaluate_repository(context, intent, context_summary)
                evaluations.append(evaluation)
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
