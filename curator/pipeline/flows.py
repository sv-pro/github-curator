"""Prefect flows for GitHub Curator pipeline."""

from typing import Optional

from prefect import flow

from curator.core.intent_structuring import StructuredIntent
from curator.pipeline.tasks import structure_intent_task


@flow(
    name="test-intent-structuring",
    description="Test flow for intent structuring with caching",
    log_prints=True,
)
def test_intent_flow(
    theme: str,
    focus_areas: Optional[list[str]] = None,
    exclusions: Optional[list[str]] = None,
) -> StructuredIntent:
    """Test flow to verify intent structuring task and caching.

    This flow demonstrates:
    - Running a single Prefect task
    - Automatic caching based on inputs
    - Cache hit on repeated execution

    Args:
        theme: Natural language description of curation theme
        focus_areas: Optional specific areas to focus on
        exclusions: Optional criteria to exclude

    Returns:
        StructuredIntent with dimensions and indicators
    """
    print(f"\n🔍 Testing intent structuring for: '{theme}'")

    # Execute intent structuring task
    intent = structure_intent_task(
        theme=theme,
        focus_areas=focus_areas,
        exclusions=exclusions,
    )

    print("\n✅ Intent created successfully!")
    print(f"   Intent ID: {intent.intent_id}")
    print(f"   Dimensions: {len(intent.dimensions)}")
    print(
        f"   Constraints: min_stars={intent.constraints.min_stars}, "
        f"max_age={intent.constraints.max_age_months}mo"
    )

    return intent
