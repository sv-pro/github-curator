# GitHub Curator: Implementation Specification

## Project Overview

GitHub Curator is a tool for intelligent curation of GitHub repositories that serves as a living demonstration of IntentHub principles. The tool doesn't just filter projects by criteria, but embodies the principles of structuring, validation, and metacognition in its architecture.

## Core Idea

The tool is self-referential: it curates projects related to AI agents and semantic systems while using the same principles that make these projects valuable. Each curation operation becomes an example of applying IntentHub principles.

## Functional Requirements

### Primary Use Case

1. User defines a **curation theme** (e.g., "AI agents with tool use", "semantic knowledge graphs", "prompt engineering frameworks")
2. System structures the theme into a **composition of relevance dimensions**
3. System searches for repositories via GitHub API
4. For each repository, performs **metacognitive evaluation** of relevance with explicit confidence intervals
5. Results are validated and presented with full traceability of reasoning
6. System reflects on results to improve future evaluations

### Repository Filtering Criteria

**Basic maturity metrics:**
- Minimum 50 stars (configurable)
- Activity within last 6 months
- Has README
- Has license

**Semantic criteria:**
- Relevance to theme (structured assessment)
- Documentation quality
- Architectural maturity
- Demonstration of principles (for IntentHub-specific themes)

## Architectural Design

### Project Structure

```
github-curator/
├── curator/
│   ├── core/
│   │   ├── intent_structuring.py      # Intent structuring
│   │   ├── metacognitive_eval.py      # Metacognitive evaluation
│   │   ├── validation.py              # Results validation
│   │   └── reflection.py              # Reflective learning
│   ├── github/
│   │   ├── api_client.py              # GitHub API client
│   │   └── repo_analyzer.py           # Repository analysis
│   ├── knowledge/
│   │   ├── criteria_graph.py          # Evaluation criteria graph
│   │   └── evaluation_rules.py        # Validation rules
│   └── outputs/
│       ├── report_generator.py        # Report generation
│       └── trace_visualizer.py        # Reasoning visualization
├── data/
│   ├── criteria/                      # Criteria definitions
│   ├── evaluations/                   # Evaluation history
│   └── reflections/                   # Reflective insights
├── config/
│   ├── curator.yaml                   # Main configuration
│   └── github.yaml                    # GitHub API settings
├── tests/
└── docs/
```

### System Components

#### 1. Intent Structuring Module

**Purpose:** Transform natural language curation query into structured composition of dimensions.

**Input:**
```json
{
  "theme": "AI agents with autonomous decision-making",
  "focus_areas": ["architecture", "tool integration", "safety"],
  "exclusions": ["toy projects", "tutorials only"]
}
```

**Output — Structured Intent:**
```json
{
  "intent_id": "uuid",
  "theme": "AI agents with autonomous decision-making",
  "dimensions": [
    {
      "name": "architectural_maturity",
      "weight": 0.3,
      "indicators": [
        "clear separation of concerns",
        "agent loop implementation",
        "state management approach"
      ],
      "validation_rules": ["must have >3 indicators"]
    },
    {
      "name": "autonomy_level",
      "weight": 0.3,
      "indicators": [
        "decision-making framework",
        "goal decomposition",
        "self-correction mechanisms"
      ]
    },
    {
      "name": "safety_considerations",
      "weight": 0.2,
      "indicators": [
        "validation layers",
        "human-in-the-loop",
        "error handling"
      ]
    },
    {
      "name": "documentation_quality",
      "weight": 0.2,
      "indicators": [
        "architecture diagrams",
        "example usage",
        "design rationale"
      ]
    }
  ],
  "constraints": {
    "min_stars": 50,
    "max_age_months": 6,
    "requires_license": true
  }
}
```

**Key principles:**
- **Composability:** dimensions are independent and combine predictably
- **Explicitness:** each dimension has clear indicators
- **Validatability:** structure enables completeness verification

#### 2. Metacognitive Evaluation Module

**Purpose:** Evaluate repository with explicit representation of confidence and reasoning.

**Evaluation process:**

1. **Context gathering:**
   - README content
   - File structure
   - Metadata (stars, activity, language)
   - Key files (architecture.md, examples/)

2. **Assessment per dimension:**
   - Search for indicators in context
   - Assess quality of found indicators
   - Calculate confidence based on data completeness

3. **Metacognitive reflection:**
   - Is there enough context for evaluation?
   - Which dimensions have high/low confidence?
   - What additional information would improve evaluation?

**Output — Evaluation Report:**
```json
{
  "repo": "owner/name",
  "intent_id": "uuid",
  "evaluated_at": "2025-10-05T12:00:00Z",
  "overall_relevance": 0.82,
  "confidence": 0.75,
  "dimension_scores": [
    {
      "dimension": "architectural_maturity",
      "score": 0.85,
      "confidence": 0.9,
      "found_indicators": [
        {
          "indicator": "clear separation of concerns",
          "evidence": "src/ contains distinct modules: planner/, executor/, validator/",
          "location": "directory structure"
        }
      ],
      "missing_indicators": [],
      "reasoning": "Strong architectural patterns evident in code organization"
    },
    {
      "dimension": "safety_considerations",
      "score": 0.60,
      "confidence": 0.5,
      "found_indicators": [
        {
          "indicator": "error handling",
          "evidence": "try-catch blocks in main execution loop",
          "location": "src/executor/main.py:45-60"
        }
      ],
      "missing_indicators": ["validation layers", "human-in-the-loop"],
      "reasoning": "Basic error handling present, but no evidence of validation architecture"
    }
  ],
  "metacognitive_notes": {
    "context_completeness": 0.7,
    "limitations": [
      "Could not access examples/ directory to verify usage patterns",
      "No architecture documentation found for autonomy_level assessment"
    ],
    "confidence_factors": {
      "high": ["clear code structure", "comprehensive README"],
      "low": ["limited documentation on safety", "no design docs"]
    }
  },
  "recommendation": "include_with_notes",
  "notes": "Strong architectural foundation but safety aspects need verification"
}
```

**Key principles:**
- **Transparency:** each evaluation traces to specific evidence
- **Metacognition:** explicit representation of confidence and limitations
- **Structure:** formalized representation enables validation

#### 3. Validation Module

**Purpose:** Verify consistency and completeness of evaluations at all levels.

**Validation types:**

**A. Structured intent validation:**
- All dimensions have indicators
- Dimension weights sum to 1.0
- No contradictory criteria
- Constraints are non-contradictory

**B. Evaluation validation:**
- All dimensions from intent are evaluated
- Each score has justification
- Confidence aligns with completeness of found indicators
- No scores without evidence

**C. Result set validation:**
- No duplicate repositories
- Score range is distributed (not all 0.9+)
- High-confidence evaluations don't contradict basic metrics
- Result count matches expectations

**Output — Validation Report:**
```json
{
  "validation_id": "uuid",
  "timestamp": "2025-10-05T12:05:00Z",
  "intent_validation": {
    "status": "valid",
    "checks_passed": 8,
    "checks_failed": 0,
    "warnings": []
  },
  "evaluation_validation": {
    "status": "valid_with_warnings",
    "checks_passed": 15,
    "checks_failed": 0,
    "warnings": [
      {
        "repo": "owner/repo",
        "issue": "low_confidence_high_score",
        "details": "score=0.85 but confidence=0.4 for dimension 'autonomy_level'",
        "severity": "medium"
      }
    ]
  },
  "results_validation": {
    "status": "valid",
    "total_repos": 23,
    "score_distribution": {
      "0.8-1.0": 5,
      "0.6-0.8": 12,
      "0.4-0.6": 6
    },
    "confidence_distribution": {
      "0.8-1.0": 8,
      "0.6-0.8": 10,
      "0.4-0.6": 5
    }
  }
}
```

#### 4. Reflection Module

**Purpose:** Analyze patterns in evaluations to improve future curations.

**Reflection types:**

**A. Evaluation patterns:**
- Which dimensions more often have low confidence?
- Which indicators are rarely detected?
- Do certain metrics (stars, activity) correlate with evaluations?

**B. Intent quality:**
- Which dimensions proved most discriminating?
- Which indicators didn't add value?
- Are additional dimensions needed?

**C. Evaluation process:**
- Which context sources were most informative?
- Where was information most often lacking?
- Can analysis order be optimized?

**Output — Reflection Report:**
```json
{
  "reflection_id": "uuid",
  "based_on_evaluations": 23,
  "insights": [
    {
      "pattern": "low_confidence_dimension",
      "dimension": "safety_considerations",
      "frequency": 0.65,
      "reason": "Most repos don't document safety explicitly",
      "recommendation": "Add indicator: 'defensive coding patterns' detectable from code"
    },
    {
      "pattern": "unused_indicator",
      "dimension": "documentation_quality",
      "indicator": "design rationale",
      "found_frequency": 0.1,
      "recommendation": "Consider removing or replacing with 'inline code comments'"
    },
    {
      "pattern": "correlation",
      "finding": "Repos with >200 stars strongly correlate (0.85) with architectural_maturity",
      "implication": "Could use stars as pre-filter for architectural assessment"
    }
  ],
  "suggested_intent_improvements": [
    {
      "type": "add_indicator",
      "dimension": "safety_considerations",
      "indicator": "unit tests for error cases"
    },
    {
      "type": "adjust_weight",
      "dimension": "documentation_quality",
      "from": 0.2,
      "to": 0.15,
      "reason": "Less discriminating than expected"
    }
  ],
  "process_improvements": [
    {
      "recommendation": "Fetch tests/ directory for safety_considerations",
      "expected_impact": "Increase confidence by ~0.2"
    }
  ]
}
```

### Component Integration: Complete Flow

```
User Input (NL theme)
         ↓
[Intent Structuring] → structured_intent.json
         ↓
[Validation] → intent_validation.json
         ↓
[GitHub Search] → candidate_repos[]
         ↓
For each repo:
    [Context Collection] → repo_context
         ↓
    [Metacognitive Eval] → evaluation.json
         ↓
    [Validation] → eval_validation.json
         ↓
[Results Aggregation] → all_evaluations[]
         ↓
[Validation] → results_validation.json
         ↓
[Reflection] → reflection_report.json
         ↓
[Report Generation] → curated_list.md + traces/
```

## Output Formats

### 1. Curated List (Markdown)

```markdown
# Curated Repositories: AI Agents with Autonomous Decision-Making

**Curation Date:** 2025-10-05  
**Intent ID:** uuid  
**Total Evaluated:** 47 repositories  
**Included:** 23 repositories  
**Overall Confidence:** 0.78

## Methodology

This curation evaluated repositories across 4 dimensions:
- Architectural Maturity (30%)
- Autonomy Level (30%)
- Safety Considerations (20%)
- Documentation Quality (20%)

Each repository was assessed with explicit confidence intervals. Full evaluation traces available in `traces/`.

---

## Highly Recommended (0.8+ relevance, 0.7+ confidence)

### 1. owner/awesome-agent (Score: 0.87, Confidence: 0.85)

**Stars:** 234 | **Last Updated:** 2025-09-15 | **Language:** Python

**Why it's relevant:**
- **Architectural Maturity (0.90):** Clear separation between planner, executor, and validator modules with well-defined interfaces
- **Autonomy Level (0.88):** Implements hierarchical goal decomposition and self-correction through result validation
- **Safety (0.75):** Error handling present, validation layers in executor
- **Documentation (0.85):** Comprehensive README with architecture diagrams and examples

**Evidence Trail:** [View full evaluation](traces/owner-awesome-agent.json)

**Notes:** Strong overall implementation. Safety aspects could be enhanced with human-in-the-loop patterns.

---

[Continue for all repos...]

## Reflection Insights

Based on this curation, we learned:
- Safety documentation is often implicit in code rather than explicit in docs
- Repos with strong architectural patterns tend to have >150 stars
- Consider adding "test coverage" as an indicator for future curations

## Validation Report

All evaluations passed validation with 2 minor warnings. See `validation/results.json` for details.
```

### 2. Interactive Trace Viewer (HTML)

Single-page application for exploring evaluations:

- Repository list with filtering by scores/confidence
- For each repo: dimension tree → indicators → evidence
- Confidence visualization (color coding)
- Metacognitive notes
- Links between reflection and original evaluations

### 3. Machine-Readable Artifacts

```
output/
├── intent/
│   ├── structured_intent.json
│   └── validation.json
├── evaluations/
│   ├── repo1.json
│   ├── repo2.json
│   └── ...
├── validation/
│   ├── intent.json
│   ├── evaluations.json
│   └── results.json
├── reflection/
│   └── insights.json
└── reports/
    ├── curated_list.md
    └── trace_viewer.html
```

## Technical Requirements

### APIs and Dependencies

**GitHub API:**
- Repository search with filters
- README and structure retrieval
- Metadata (stars, activity, license)
- Rate limiting handling

**Python dependencies:**
- `requests` or `PyGithub` for GitHub API
- `pyyaml` for configuration
- `jinja2` for report templates
- Claude API client for metacognitive evaluations

### Configuration

**curator.yaml:**
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

github:
  search_limit: 100
  context_files:
    - README.md
    - ARCHITECTURE.md
    - docs/
    - examples/
  rate_limit_buffer: 10

evaluation:
  confidence_threshold_high: 0.7
  confidence_threshold_low: 0.4
  min_indicators_found: 2

validation:
  strict_mode: false
  fail_on_warnings: false

reflection:
  min_evaluations_for_patterns: 10
  correlation_threshold: 0.7

output:
  formats:
    - markdown
    - json
    - html_trace
  trace_detail: full
```

## Demonstration of IntentHub Principles

### Structuring → Validation → Metacognition

**Structuring:**
- Natural language theme → composition of dimensions
- Dimensions → indicators → evidence
- Criteria graph as explicit knowledge

**Validation:**
- Intent validated for completeness
- Each evaluation validated for consistency
- Results validated for distribution

**Metacognition:**
- Explicit confidence at every level
- Identification of limitations and gaps
- Understanding of own evaluation quality

### Transparency and Traceability

- Every evaluation claim traces to specific evidence
- Visualization of reasoning chain
- Machine-readable traces for auditing

### Reflective Learning

- Pattern analysis in evaluations
- Suggestions for criteria improvement
- Intent evolution through experience

### Reliability Through Independent Assessments

- Ability to run multiple evaluations in parallel with different weights
- Result comparison to identify parameter sensitivity
- Explicit representation of uncertainty

### Self-Referentiality

The tool itself can be evaluated by its own criteria:
- Architectural maturity: module separation
- Transparency: trace generation
- Metacognition: confidence tracking
- Reflection: reflection module

## Evolution and Extensions

### Phase 1: Basic Functionality
- Intent structuring for single theme
- Evaluation by fixed dimensions
- Simple validation
- Markdown report

### Phase 2: Metacognition
- Confidence tracking
- Limitation identification
- Metacognitive notes
- Interactive trace viewer

### Phase 3: Reflection
- Pattern detection
- Intent improvement suggestions
- Process optimization
- Historical comparison

### Phase 4: Composition (future)
- Intent combination
- Comparative curation
- Criteria evolution through feedback
- Community-driven intent library

## Success Criteria

**Functional:**
- [ ] Successfully structures 5+ different themes
- [ ] Evaluates 20+ repositories per minute
- [ ] Generates readable Markdown with traceability
- [ ] Identifies relevant repositories (precision >0.7)

**Architectural (principle demonstration):**
- [ ] Each evaluation traces to evidence
- [ ] Explicit confidence representation at all levels
- [ ] Validation detects inconsistencies
- [ ] Reflection suggests real improvements

**Self-referential:**
- [ ] Tool itself passes evaluation by its own criteria
- [ ] Code demonstrates architectural maturity
- [ ] Documentation meets standards it checks
- [ ] Community finds tool through curation of similar projects

---

This document provides sufficient detail for Claude Code to generate a working prototype with correct architecture that demonstrates key IntentHub principles through a concrete practical task.