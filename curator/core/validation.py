"""Validation module - verifies consistency and completeness at all levels."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import yaml

from curator.core.intent_structuring import StructuredIntent
from curator.core.metacognitive_eval import EvaluationReport


@dataclass
class ValidationCheck:
    """A single validation check result."""
    check_name: str
    passed: bool
    message: str
    severity: str = "info"  # info, warning, error


@dataclass
class IntentValidation:
    """Validation results for structured intent."""
    status: str
    checks_passed: int
    checks_failed: int
    warnings: List[ValidationCheck] = field(default_factory=list)
    errors: List[ValidationCheck] = field(default_factory=list)


@dataclass
class EvaluationValidation:
    """Validation results for single evaluation."""
    status: str
    checks_passed: int
    checks_failed: int
    warnings: List[ValidationCheck] = field(default_factory=list)
    errors: List[ValidationCheck] = field(default_factory=list)


@dataclass
class ResultsValidation:
    """Validation results for complete result set."""
    status: str
    total_repos: int
    score_distribution: Dict[str, int]
    confidence_distribution: Dict[str, int]
    checks_passed: int
    checks_failed: int
    warnings: List[ValidationCheck] = field(default_factory=list)


@dataclass
class ValidationReport:
    """Complete validation report."""
    validation_id: str
    timestamp: str
    intent_validation: IntentValidation
    evaluation_validations: List[EvaluationValidation]
    results_validation: ResultsValidation

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "validation_id": self.validation_id,
            "timestamp": self.timestamp,
            "intent_validation": {
                "status": self.intent_validation.status,
                "checks_passed": self.intent_validation.checks_passed,
                "checks_failed": self.intent_validation.checks_failed,
                "warnings": [
                    {"check": w.check_name, "message": w.message, "severity": w.severity}
                    for w in self.intent_validation.warnings
                ],
                "errors": [
                    {"check": e.check_name, "message": e.message, "severity": e.severity}
                    for e in self.intent_validation.errors
                ]
            },
            "results_validation": {
                "status": self.results_validation.status,
                "total_repos": self.results_validation.total_repos,
                "score_distribution": self.results_validation.score_distribution,
                "confidence_distribution": self.results_validation.confidence_distribution,
                "checks_passed": self.results_validation.checks_passed,
                "checks_failed": self.results_validation.checks_failed,
                "warnings": [
                    {"check": w.check_name, "message": w.message, "severity": w.severity}
                    for w in self.results_validation.warnings
                ]
            }
        }


class Validator:
    """Validates intent structure, evaluations, and results."""

    def __init__(self, config_path: str = "config/curator.yaml"):
        """Initialize validator."""
        self.config = self._load_config(config_path)
        self.strict_mode = self.config['validation']['strict_mode']
        self.fail_on_warnings = self.config['validation']['fail_on_warnings']

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def validate_intent(self, intent: StructuredIntent) -> IntentValidation:
        """Validate structured intent.

        Args:
            intent: StructuredIntent to validate

        Returns:
            IntentValidation with check results
        """
        checks = []
        warnings = []
        errors = []

        # Check 1: All dimensions have indicators
        for dim in intent.dimensions:
            if not dim.indicators:
                errors.append(ValidationCheck(
                    check_name="dimension_has_indicators",
                    passed=False,
                    message=f"Dimension '{dim.name}' has no indicators",
                    severity="error"
                ))
            else:
                checks.append(ValidationCheck(
                    check_name=f"dimension_{dim.name}_has_indicators",
                    passed=True,
                    message=f"Dimension '{dim.name}' has {len(dim.indicators)} indicators",
                    severity="info"
                ))

        # Check 2: Dimension weights sum to 1.0 (within tolerance)
        total_weight = sum(d.weight for d in intent.dimensions)
        if abs(total_weight - 1.0) > 0.01:
            errors.append(ValidationCheck(
                check_name="weights_sum_to_one",
                passed=False,
                message=f"Dimension weights sum to {total_weight}, expected 1.0",
                severity="error"
            ))
        else:
            checks.append(ValidationCheck(
                check_name="weights_sum_to_one",
                passed=True,
                message="Dimension weights sum to 1.0",
                severity="info"
            ))

        # Check 3: No dimension has zero weight
        for dim in intent.dimensions:
            if dim.weight <= 0:
                warnings.append(ValidationCheck(
                    check_name=f"dimension_{dim.name}_positive_weight",
                    passed=False,
                    message=f"Dimension '{dim.name}' has zero or negative weight",
                    severity="warning"
                ))

        # Check 4: Reasonable number of dimensions (3-6)
        num_dims = len(intent.dimensions)
        if num_dims < 3:
            warnings.append(ValidationCheck(
                check_name="dimension_count",
                passed=False,
                message=f"Only {num_dims} dimensions - consider adding more for comprehensive evaluation",
                severity="warning"
            ))
        elif num_dims > 6:
            warnings.append(ValidationCheck(
                check_name="dimension_count",
                passed=False,
                message=f"{num_dims} dimensions - may be too complex",
                severity="warning"
            ))
        else:
            checks.append(ValidationCheck(
                check_name="dimension_count",
                passed=True,
                message=f"{num_dims} dimensions is appropriate",
                severity="info"
            ))

        # Determine status
        checks_passed = len([c for c in checks if c.passed])
        checks_failed = len(errors)

        if errors:
            status = "invalid"
        elif warnings and self.fail_on_warnings:
            status = "invalid"
        elif warnings:
            status = "valid_with_warnings"
        else:
            status = "valid"

        return IntentValidation(
            status=status,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            warnings=warnings,
            errors=errors
        )

    def validate_evaluation(self, evaluation: EvaluationReport, intent: StructuredIntent) -> EvaluationValidation:
        """Validate single evaluation.

        Args:
            evaluation: EvaluationReport to validate
            intent: Original StructuredIntent

        Returns:
            EvaluationValidation with check results
        """
        checks = []
        warnings = []
        errors = []

        # Check 1: All dimensions from intent are evaluated
        intent_dims = {d.name for d in intent.dimensions}
        eval_dims = {ds.dimension for ds in evaluation.dimension_scores}

        missing_dims = intent_dims - eval_dims
        if missing_dims:
            errors.append(ValidationCheck(
                check_name="all_dimensions_evaluated",
                passed=False,
                message=f"Missing evaluations for dimensions: {', '.join(missing_dims)}",
                severity="error"
            ))
        else:
            checks.append(ValidationCheck(
                check_name="all_dimensions_evaluated",
                passed=True,
                message="All dimensions evaluated",
                severity="info"
            ))

        # Check 2: Each dimension has justification
        for ds in evaluation.dimension_scores:
            if not ds.reasoning:
                warnings.append(ValidationCheck(
                    check_name=f"dimension_{ds.dimension}_has_reasoning",
                    passed=False,
                    message=f"Dimension '{ds.dimension}' lacks reasoning",
                    severity="warning"
                ))

        # Check 3: Confidence aligns with found indicators
        min_indicators = self.config['evaluation'].get('min_indicators_found', 2)
        for ds in evaluation.dimension_scores:
            num_found = len(ds.found_indicators)
            if num_found < min_indicators and ds.confidence > 0.7:
                warnings.append(ValidationCheck(
                    check_name=f"confidence_indicator_alignment_{ds.dimension}",
                    passed=False,
                    message=f"High confidence ({ds.confidence}) with only {num_found} indicators for '{ds.dimension}'",
                    severity="warning"
                ))

        # Check 4: No scores without evidence
        for ds in evaluation.dimension_scores:
            if ds.score > 0.5 and not ds.found_indicators:
                errors.append(ValidationCheck(
                    check_name=f"score_has_evidence_{ds.dimension}",
                    passed=False,
                    message=f"Score {ds.score} for '{ds.dimension}' without any evidence",
                    severity="error"
                ))

        # Check 5: Scores in valid range
        if not (0.0 <= evaluation.overall_relevance <= 1.0):
            errors.append(ValidationCheck(
                check_name="overall_score_range",
                passed=False,
                message=f"Overall relevance {evaluation.overall_relevance} out of range [0, 1]",
                severity="error"
            ))

        # Determine status
        checks_passed = len([c for c in checks if c.passed])
        checks_failed = len(errors)

        if errors:
            status = "invalid"
        elif warnings and self.fail_on_warnings:
            status = "invalid"
        elif warnings:
            status = "valid_with_warnings"
        else:
            status = "valid"

        return EvaluationValidation(
            status=status,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            warnings=warnings,
            errors=errors
        )

    def validate_results(self, evaluations: List[EvaluationReport]) -> ResultsValidation:
        """Validate complete result set.

        Args:
            evaluations: List of all evaluations

        Returns:
            ResultsValidation with check results
        """
        warnings = []
        checks_passed = 0
        checks_failed = 0

        # Calculate score distribution
        score_dist = {"0.8-1.0": 0, "0.6-0.8": 0, "0.4-0.6": 0, "0.0-0.4": 0}
        for eval in evaluations:
            score = eval.overall_relevance
            if score >= 0.8:
                score_dist["0.8-1.0"] += 1
            elif score >= 0.6:
                score_dist["0.6-0.8"] += 1
            elif score >= 0.4:
                score_dist["0.4-0.6"] += 1
            else:
                score_dist["0.0-0.4"] += 1

        # Calculate confidence distribution
        conf_dist = {"0.8-1.0": 0, "0.6-0.8": 0, "0.4-0.6": 0, "0.0-0.4": 0}
        for eval in evaluations:
            conf = eval.confidence
            if conf >= 0.8:
                conf_dist["0.8-1.0"] += 1
            elif conf >= 0.6:
                conf_dist["0.6-0.8"] += 1
            elif conf >= 0.4:
                conf_dist["0.4-0.6"] += 1
            else:
                conf_dist["0.0-0.4"] += 1

        # Check 1: No duplicate repositories
        repo_names = [e.repo for e in evaluations]
        if len(repo_names) != len(set(repo_names)):
            warnings.append(ValidationCheck(
                check_name="no_duplicates",
                passed=False,
                message="Duplicate repositories found in results",
                severity="warning"
            ))
            checks_failed += 1
        else:
            checks_passed += 1

        # Check 2: Score distribution
        total = len(evaluations)
        if total > 0:
            high_score_pct = score_dist["0.8-1.0"] / total
            if high_score_pct > 0.8:
                warnings.append(ValidationCheck(
                    check_name="score_distribution",
                    passed=False,
                    message=f"{high_score_pct*100:.0f}% of repos scored 0.8+ - may indicate insufficient discrimination",
                    severity="warning"
                ))

        # Check 3: Confidence levels
        if total > 0:
            low_conf_pct = conf_dist["0.0-0.4"] / total
            if low_conf_pct > 0.5:
                warnings.append(ValidationCheck(
                    check_name="confidence_levels",
                    passed=False,
                    message=f"{low_conf_pct*100:.0f}% of evaluations have low confidence (<0.4)",
                    severity="warning"
                ))

        status = "valid" if not warnings else "valid_with_warnings"

        return ResultsValidation(
            status=status,
            total_repos=len(evaluations),
            score_distribution=score_dist,
            confidence_distribution=conf_dist,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            warnings=warnings
        )

    def validate_all(
        self,
        intent: StructuredIntent,
        evaluations: List[EvaluationReport]
    ) -> ValidationReport:
        """Validate intent, evaluations, and results.

        Args:
            intent: StructuredIntent
            evaluations: List of evaluations

        Returns:
            Complete ValidationReport
        """
        import uuid

        intent_validation = self.validate_intent(intent)

        evaluation_validations = [
            self.validate_evaluation(eval, intent)
            for eval in evaluations
        ]

        results_validation = self.validate_results(evaluations)

        return ValidationReport(
            validation_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            intent_validation=intent_validation,
            evaluation_validations=evaluation_validations,
            results_validation=results_validation
        )
