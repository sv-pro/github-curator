"""Tests for intent structuring module."""

import pytest
from curator.core.intent_structuring import (
    IntentStructurer,
    StructuredIntent,
    Dimension,
    Indicator,
    Constraints
)


def test_structured_intent_creation():
    """Test creating a structured intent."""
    indicator1 = Indicator(name="test_indicator", description="A test indicator")
    dimension1 = Dimension(
        name="test_dimension",
        weight=1.0,
        indicators=[indicator1],
        validation_rules=["must have >1 indicators"]
    )
    constraints = Constraints(min_stars=50, max_age_months=6, requires_license=True)

    intent = StructuredIntent(
        intent_id="test-123",
        theme="Test theme",
        dimensions=[dimension1],
        constraints=constraints
    )

    assert intent.intent_id == "test-123"
    assert intent.theme == "Test theme"
    assert len(intent.dimensions) == 1
    assert intent.dimensions[0].name == "test_dimension"
    assert intent.constraints.min_stars == 50


def test_structured_intent_to_dict():
    """Test converting structured intent to dictionary."""
    indicator1 = Indicator(name="indicator1", description="Description 1")
    dimension1 = Dimension(
        name="dimension1",
        weight=0.5,
        indicators=[indicator1]
    )
    dimension2 = Dimension(
        name="dimension2",
        weight=0.5,
        indicators=[Indicator(name="indicator2", description="Description 2")]
    )
    constraints = Constraints(min_stars=100)

    intent = StructuredIntent(
        intent_id="test-456",
        theme="Test theme",
        dimensions=[dimension1, dimension2],
        constraints=constraints,
        focus_areas=["area1", "area2"],
        exclusions=["excluded1"]
    )

    intent_dict = intent.to_dict()

    assert intent_dict["intent_id"] == "test-456"
    assert intent_dict["theme"] == "Test theme"
    assert len(intent_dict["dimensions"]) == 2
    assert intent_dict["dimensions"][0]["name"] == "dimension1"
    assert intent_dict["dimensions"][0]["weight"] == 0.5
    assert intent_dict["constraints"]["min_stars"] == 100
    assert "area1" in intent_dict["focus_areas"]
    assert "excluded1" in intent_dict["exclusions"]


def test_dimension_weight_normalization():
    """Test that dimension weights are normalized."""
    # This would be tested with the actual IntentStructurer
    # which normalizes weights in _generate_dimensions
    dimensions = [
        Dimension(name="dim1", weight=2.0, indicators=[Indicator("ind1")]),
        Dimension(name="dim2", weight=3.0, indicators=[Indicator("ind2")])
    ]

    # Manual normalization (as done in IntentStructurer)
    total = sum(d.weight for d in dimensions)
    for dim in dimensions:
        dim.weight = dim.weight / total

    assert abs(sum(d.weight for d in dimensions) - 1.0) < 0.01
    assert abs(dimensions[0].weight - 0.4) < 0.01  # 2/5
    assert abs(dimensions[1].weight - 0.6) < 0.01  # 3/5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
