"""Quickstart example for GitHub Curator.

This example demonstrates basic usage without the CLI.
"""

import os
from curator.core.intent_structuring import IntentStructurer
from curator.github.api_client import GitHubAPIClient
from curator.github.repo_analyzer import RepositoryAnalyzer
from curator.core.metacognitive_eval import MetacognitiveEvaluator
from curator.core.validation import Validator
from curator.core.reflection import Reflector
from curator.outputs.report_generator import ReportGenerator


def main():
    """Run a simple curation example."""

    # Check environment variables
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set")
        return

    if not os.getenv("GITHUB_TOKEN"):
        print("Error: GITHUB_TOKEN not set")
        return

    print("🔍 GitHub Curator Quickstart Example")
    print("=" * 50)

    # Theme to curate
    theme = "Python CLI tools for developers"
    print(f"\nTheme: {theme}")

    # Initialize components
    print("\nInitializing components...")
    structurer = IntentStructurer()
    github_client = GitHubAPIClient()
    analyzer = RepositoryAnalyzer(github_client)
    evaluator = MetacognitiveEvaluator()
    validator = Validator()
    reflector = Reflector()
    report_gen = ReportGenerator("output/quickstart")

    # Structure the intent
    print("📋 Structuring intent...")
    intent = structurer.structure_theme(
        theme=theme,
        focus_areas=["usability", "documentation"],
        exclusions=["abandoned projects"]
    )

    print(f"   Created {len(intent.dimensions)} dimensions:")
    for dim in intent.dimensions:
        print(f"   - {dim.name} ({dim.weight*100:.0f}%)")

    # Validate intent
    print("\n✅ Validating intent...")
    intent_validation = validator.validate_intent(intent)
    print(f"   Status: {intent_validation.status}")

    # Search repositories (limit to 5 for quick demo)
    print("\n🔎 Searching GitHub (limit: 5)...")
    repos = github_client.search_repositories(
        query=theme,
        min_stars=100,
        max_age_months=12,
        limit=5
    )
    print(f"   Found {len(repos)} repositories")

    # Evaluate repositories
    print("\n🧠 Evaluating repositories...")
    evaluations = []

    for i, repo in enumerate(repos, 1):
        print(f"   [{i}/{len(repos)}] {repo.full_name}...")

        # Gather context
        context = analyzer.analyze_repository(repo)
        context_summary = analyzer.get_evaluation_context_summary(context)

        # Evaluate
        evaluation = evaluator.evaluate_repository(context, intent, context_summary)
        evaluations.append(evaluation)

        print(f"       Score: {evaluation.overall_relevance:.2f}, Confidence: {evaluation.confidence:.2f}")

    # Validate results
    print("\n✅ Validating results...")
    validation_report = validator.validate_all(intent, evaluations)
    print(f"   Status: {validation_report.results_validation.status}")

    # Reflect on patterns
    print("\n🤔 Analyzing patterns...")
    reflection = reflector.reflect(evaluations, intent)
    print(f"   Found {len(reflection.insights)} insights")

    # Generate reports
    print("\n📝 Generating reports...")

    # Save JSON
    json_paths = report_gen.save_json_artifacts(
        intent, evaluations, validation_report, reflection
    )
    print(f"   ✓ JSON artifacts saved")

    # Generate markdown
    md_path = report_gen.generate_markdown_report(
        intent, evaluations, validation_report, reflection
    )
    print(f"   ✓ Markdown report: {md_path}")

    # Generate HTML trace
    html_path = report_gen.generate_html_trace_viewer(intent, evaluations)
    print(f"   ✓ HTML trace viewer: {html_path}")

    # Show top results
    print("\n🌟 Top Results:")
    top_repos = sorted(
        evaluations,
        key=lambda e: (e.overall_relevance, e.confidence),
        reverse=True
    )

    for i, eval in enumerate(top_repos, 1):
        print(f"\n   {i}. {eval.repo}")
        print(f"      Overall: {eval.overall_relevance:.2f} (confidence: {eval.confidence:.2f})")
        print(f"      Recommendation: {eval.recommendation}")

        # Show top dimension
        top_dim = max(eval.dimension_scores, key=lambda d: d.score)
        print(f"      Strongest: {top_dim.dimension} ({top_dim.score:.2f})")

    print("\n✨ Quickstart complete!")
    print(f"\nView results in: output/quickstart/")


if __name__ == "__main__":
    main()
