"""Prefect tasks for GitHub Curator pipeline."""

from datetime import timedelta
from typing import Optional

from prefect import task
from prefect.tasks import exponential_backoff

from curator.core.intent_structuring import IntentStructurer, StructuredIntent
from curator.pipeline.cache import intent_cache_key
from curator.pipeline.config import PrefectConfig

# Load Prefect configuration
_prefect_config = PrefectConfig()
_intent_config = _prefect_config.get_task_config("structure_intent")


@task(
    name="structure-intent",
    description="Structure natural language theme into formal intent with dimensions",
    cache_key_fn=intent_cache_key,
    cache_expiration=timedelta(seconds=_intent_config["cache_expiration"]),
    retries=_intent_config["retries"],
    retry_delay_seconds=exponential_backoff(backoff_factor=2),
    tags=["intent", "llm", "structuring"],
    persist_result=True,
)
def structure_intent_task(
    theme: str,
    focus_areas: Optional[list[str]] = None,
    exclusions: Optional[list[str]] = None,
    config_path: str = "config/curator.yaml",
) -> StructuredIntent:
    """Structure a natural language theme into a formal intent.

    This task converts a natural language curation theme (e.g., "AI agents with tool use")
    into a structured intent with evaluation dimensions, indicators, and constraints.

    Args:
        theme: Natural language description of curation theme
        focus_areas: Optional specific areas to focus on
        exclusions: Optional criteria to exclude
        config_path: Path to curator configuration file

    Returns:
        StructuredIntent with dimensions, indicators, and constraints

    Caching:
        Results are cached for 7 days based on the theme, focus areas, exclusions,
        and configuration file version. Cache is automatically invalidated when
        the configuration changes.
    """
    from prefect import get_run_logger

    logger = get_run_logger()
    logger.info(f"Structuring intent for theme: {theme}")

    if focus_areas:
        logger.info(f"Focus areas: {', '.join(focus_areas)}")
    if exclusions:
        logger.info(f"Exclusions: {', '.join(exclusions)}")

    # Use existing IntentStructurer implementation
    structurer = IntentStructurer(config_path)
    intent = structurer.structure_theme(
        theme=theme,
        focus_areas=focus_areas,
        exclusions=exclusions,
    )

    logger.info(f"Created intent with ID: {intent.intent_id}")
    logger.info(f"Dimensions: {len(intent.dimensions)}")
    for dim in intent.dimensions:
        logger.debug(
            f"  - {dim.name} ({dim.weight*100:.0f}%) with {len(dim.indicators)} indicators"
        )

    return intent
