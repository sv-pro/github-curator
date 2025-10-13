"""Intent structuring module - transforms natural language themes into structured evaluations."""

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml


@dataclass
class Indicator:
    """A specific indicator for an evaluation dimension."""

    name: str
    description: str = ""


@dataclass
class Dimension:
    """An evaluation dimension with indicators and weight."""

    name: str
    weight: float
    indicators: list[Indicator]
    validation_rules: list[str] = field(default_factory=list)


@dataclass
class Constraints:
    """Repository filtering constraints."""

    min_stars: int = 50
    max_age_months: int = 6
    requires_license: bool = True


@dataclass
class StructuredIntent:
    """A structured intent representing a curation theme."""

    intent_id: str
    theme: str
    dimensions: list[Dimension]
    constraints: Constraints
    focus_areas: list[str] = field(default_factory=list)
    exclusions: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "intent_id": self.intent_id,
            "theme": self.theme,
            "dimensions": [
                {
                    "name": dim.name,
                    "weight": dim.weight,
                    "indicators": [
                        {"name": ind.name, "description": ind.description} for ind in dim.indicators
                    ],
                    "validation_rules": dim.validation_rules,
                }
                for dim in self.dimensions
            ],
            "constraints": {
                "min_stars": self.constraints.min_stars,
                "max_age_months": self.constraints.max_age_months,
                "requires_license": self.constraints.requires_license,
            },
            "focus_areas": self.focus_areas,
            "exclusions": self.exclusions,
            "created_at": self.created_at,
        }


class IntentStructurer:
    """Structures natural language curation themes into dimensional evaluations."""

    def __init__(self, config_path: str = "config/curator.yaml", cache_dir: str = ".cache/intents"):
        """Initialize with configuration."""
        self.config = self._load_config(config_path)
        self.config_path = config_path
        # Use fallback-enabled LLM provider from config
        from curator.llm import create_llm_provider_from_config

        self.llm_provider = create_llm_provider_from_config(config_path)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self, config_path: str) -> dict[str, Any]:
        """Load configuration from YAML file."""
        with open(config_path) as f:
            return yaml.safe_load(f)

    def _get_cache_key(
        self,
        theme: str,
        focus_areas: Optional[list[str]],
        exclusions: Optional[list[str]],
        custom_weights: Optional[dict[str, float]],
    ) -> str:
        """Generate cache key from theme parameters."""
        cache_data = {
            "theme": theme,
            "focus_areas": sorted(focus_areas) if focus_areas else [],
            "exclusions": sorted(exclusions) if exclusions else [],
            "custom_weights": custom_weights or {},
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_str.encode()).hexdigest()

    def _load_from_cache(self, cache_key: str) -> Optional[StructuredIntent]:
        """Load structured intent from cache if available."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            print(f"💾 Loading cached intent from {cache_file.name}")
            with open(cache_file) as f:
                data = json.load(f)
                return self._dict_to_intent(data)
        return None

    def _save_to_cache(self, cache_key: str, intent: StructuredIntent):
        """Save structured intent to cache."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        print(f"💾 Saving intent to cache: {cache_file.name}")
        with open(cache_file, "w") as f:
            json.dump(intent.to_dict(), f, indent=2)

    def _dict_to_intent(self, data: dict[str, Any]) -> StructuredIntent:
        """Convert dictionary to StructuredIntent object."""
        dimensions = [
            Dimension(
                name=dim["name"],
                weight=dim["weight"],
                indicators=[Indicator(**ind) for ind in dim["indicators"]],
                validation_rules=dim.get("validation_rules", []),
            )
            for dim in data["dimensions"]
        ]
        constraints = Constraints(**data["constraints"])
        return StructuredIntent(
            intent_id=data["intent_id"],
            theme=data["theme"],
            dimensions=dimensions,
            constraints=constraints,
            focus_areas=data.get("focus_areas", []),
            exclusions=data.get("exclusions", []),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
        )

    def structure_theme(
        self,
        theme: str,
        focus_areas: Optional[list[str]] = None,
        exclusions: Optional[list[str]] = None,
        custom_weights: Optional[dict[str, float]] = None,
    ) -> StructuredIntent:
        """Structure a natural language theme into a formal intent.

        Args:
            theme: Natural language description of curation theme
            focus_areas: Optional specific areas to focus on
            exclusions: Optional criteria to exclude
            custom_weights: Optional custom dimension weights

        Returns:
            StructuredIntent with dimensions, indicators, and constraints
        """
        # Check cache first
        cache_key = self._get_cache_key(theme, focus_areas, exclusions, custom_weights)
        cached_intent = self._load_from_cache(cache_key)
        if cached_intent:
            return cached_intent

        # Generate structured dimensions using Claude
        print("🤖 Generating new intent structure with Claude...")
        dimensions = self._generate_dimensions(theme, focus_areas, exclusions, custom_weights)

        # Get constraints from config
        constraints = Constraints(
            min_stars=self.config["intent"]["constraints"]["min_stars"],
            max_age_months=self.config["intent"]["constraints"]["max_age_months"],
            requires_license=self.config["intent"]["constraints"]["requires_license"],
        )

        intent = StructuredIntent(
            intent_id=str(uuid.uuid4()),
            theme=theme,
            dimensions=dimensions,
            constraints=constraints,
            focus_areas=focus_areas or [],
            exclusions=exclusions or [],
        )

        # Save to cache
        self._save_to_cache(cache_key, intent)

        return intent

    def _generate_dimensions(
        self,
        theme: str,
        focus_areas: Optional[list[str]],
        exclusions: Optional[list[str]],
        custom_weights: Optional[dict[str, float]],
    ) -> list[Dimension]:
        """Use Claude to generate evaluation dimensions for the theme."""

        focus_text = f"\nFocus areas: {', '.join(focus_areas)}" if focus_areas else ""
        exclusion_text = f"\nExclusions: {', '.join(exclusions)}" if exclusions else ""

        prompt = f"""You are structuring a GitHub repository curation theme into formal evaluation dimensions.

Theme: {theme}{focus_text}{exclusion_text}

Generate 3-5 evaluation dimensions that would be used to assess repositories for this theme. Each dimension should:
1. Be specific and measurable
2. Have 3-5 concrete indicators that can be found in repository structure/documentation
3. Be independent from other dimensions
4. Contribute to overall relevance assessment

Common dimension types to consider:
- Architectural maturity (code structure, patterns)
- Technical depth (algorithms, implementation quality)
- Documentation quality (README, examples, architecture docs)
- Practical usability (installation, examples, API clarity)
- Community engagement (issues, PRs, maintenance)
- Safety/reliability (testing, error handling, validation)

Return your response as a JSON array of dimensions with this structure:
{{
  "dimensions": [
    {{
      "name": "dimension_name",
      "description": "what this dimension measures",
      "weight": 0.3,
      "indicators": [
        {{"name": "indicator1", "description": "what to look for"}},
        {{"name": "indicator2", "description": "what to look for"}}
      ],
      "validation_rules": ["must have >2 indicators"]
    }}
  ]
}}

Ensure weights sum to 1.0. Make indicators specific and detectable."""

        # Use fallback-enabled LLM provider
        from curator.llm.base import LLMMessage

        response = self.llm_provider.complete(
            messages=[LLMMessage(role="user", content=prompt)],
            max_tokens=2000,
        )

        # Parse LLM response
        import json

        response_text = response.content

        # Extract JSON from response
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}") + 1
        json_text = response_text[start_idx:end_idx]

        data = json.loads(json_text)

        # Convert to Dimension objects
        dimensions = []
        for dim_data in data["dimensions"]:
            # Apply custom weights if provided
            weight = (
                custom_weights.get(dim_data["name"], dim_data["weight"])
                if custom_weights
                else dim_data["weight"]
            )

            indicators = [
                Indicator(name=ind["name"], description=ind.get("description", ""))
                for ind in dim_data["indicators"]
            ]

            dimensions.append(
                Dimension(
                    name=dim_data["name"],
                    weight=weight,
                    indicators=indicators,
                    validation_rules=dim_data.get("validation_rules", []),
                )
            )

        # Normalize weights to sum to 1.0
        total_weight = sum(d.weight for d in dimensions)
        for dim in dimensions:
            dim.weight = dim.weight / total_weight

        return dimensions
