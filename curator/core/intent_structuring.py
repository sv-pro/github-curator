"""Intent structuring module - transforms natural language themes into structured evaluations."""

import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import anthropic
import yaml
import os


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
    indicators: List[Indicator]
    validation_rules: List[str] = field(default_factory=list)


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
    dimensions: List[Dimension]
    constraints: Constraints
    focus_areas: List[str] = field(default_factory=list)
    exclusions: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "intent_id": self.intent_id,
            "theme": self.theme,
            "dimensions": [
                {
                    "name": dim.name,
                    "weight": dim.weight,
                    "indicators": [{"name": ind.name, "description": ind.description} for ind in dim.indicators],
                    "validation_rules": dim.validation_rules
                }
                for dim in self.dimensions
            ],
            "constraints": {
                "min_stars": self.constraints.min_stars,
                "max_age_months": self.constraints.max_age_months,
                "requires_license": self.constraints.requires_license
            },
            "focus_areas": self.focus_areas,
            "exclusions": self.exclusions,
            "created_at": self.created_at
        }


class IntentStructurer:
    """Structures natural language curation themes into dimensional evaluations."""

    def __init__(self, config_path: str = "config/curator.yaml"):
        """Initialize with configuration."""
        self.config = self._load_config(config_path)
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def structure_theme(
        self,
        theme: str,
        focus_areas: Optional[List[str]] = None,
        exclusions: Optional[List[str]] = None,
        custom_weights: Optional[Dict[str, float]] = None
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
        # Generate structured dimensions using Claude
        dimensions = self._generate_dimensions(theme, focus_areas, exclusions, custom_weights)

        # Get constraints from config
        constraints = Constraints(
            min_stars=self.config['intent']['constraints']['min_stars'],
            max_age_months=self.config['intent']['constraints']['max_age_months'],
            requires_license=self.config['intent']['constraints']['requires_license']
        )

        return StructuredIntent(
            intent_id=str(uuid.uuid4()),
            theme=theme,
            dimensions=dimensions,
            constraints=constraints,
            focus_areas=focus_areas or [],
            exclusions=exclusions or []
        )

    def _generate_dimensions(
        self,
        theme: str,
        focus_areas: Optional[List[str]],
        exclusions: Optional[List[str]],
        custom_weights: Optional[Dict[str, float]]
    ) -> List[Dimension]:
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

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse Claude's response
        import json
        response_text = response.content[0].text

        # Extract JSON from response
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        json_text = response_text[start_idx:end_idx]

        data = json.loads(json_text)

        # Convert to Dimension objects
        dimensions = []
        for dim_data in data['dimensions']:
            # Apply custom weights if provided
            weight = custom_weights.get(dim_data['name'], dim_data['weight']) if custom_weights else dim_data['weight']

            indicators = [
                Indicator(name=ind['name'], description=ind.get('description', ''))
                for ind in dim_data['indicators']
            ]

            dimensions.append(Dimension(
                name=dim_data['name'],
                weight=weight,
                indicators=indicators,
                validation_rules=dim_data.get('validation_rules', [])
            ))

        # Normalize weights to sum to 1.0
        total_weight = sum(d.weight for d in dimensions)
        for dim in dimensions:
            dim.weight = dim.weight / total_weight

        return dimensions
