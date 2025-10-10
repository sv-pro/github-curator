#!/usr/bin/env python3
"""
Phase Gate Test Runner

Runs comprehensive tests between development phases/features/stages.
This script ensures quality gates are met before progressing to the next phase.

Usage:
    python scripts/run_phase_gate_tests.py [--phase PHASE] [--strict] [--coverage-min N]

Examples:
    # Run all tests for Phase 2
    python scripts/run_phase_gate_tests.py --phase 2

    # Run with strict mode (fail on any warning)
    python scripts/run_phase_gate_tests.py --strict

    # Require minimum 80% coverage
    python scripts/run_phase_gate_tests.py --coverage-min 80
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Optional


class Color:
    """Terminal colors."""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


class PhaseGateRunner:
    """Phase gate test runner."""

    def __init__(
        self,
        phase: Optional[str] = None,
        strict: bool = False,
        coverage_min: int = 70,
        verbose: bool = False,
    ):
        self.phase = phase
        self.strict = strict
        self.coverage_min = coverage_min
        self.verbose = verbose
        self.project_root = Path(__file__).parent.parent
        self.results: dict[str, bool] = {}

    def print_header(self, text: str):
        """Print section header."""
        print(f"\n{Color.BOLD}{Color.HEADER}{'=' * 80}{Color.ENDC}")
        print(f"{Color.BOLD}{Color.HEADER}{text:^80}{Color.ENDC}")
        print(f"{Color.BOLD}{Color.HEADER}{'=' * 80}{Color.ENDC}\n")

    def print_success(self, text: str):
        """Print success message."""
        print(f"{Color.OKGREEN}✓ {text}{Color.ENDC}")

    def print_failure(self, text: str):
        """Print failure message."""
        print(f"{Color.FAIL}✗ {text}{Color.ENDC}")

    def print_warning(self, text: str):
        """Print warning message."""
        print(f"{Color.WARNING}⚠ {text}{Color.ENDC}")

    def print_info(self, text: str):
        """Print info message."""
        print(f"{Color.OKCYAN}ℹ {text}{Color.ENDC}")

    def run_command(self, cmd: list[str], name: str) -> bool:
        """Run a command and capture result."""
        self.print_info(f"Running: {name}")
        print(f"  Command: {' '.join(cmd)}\n")

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=not self.verbose,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                self.print_success(f"{name} passed")
                if self.verbose and result.stdout:
                    print(result.stdout)
                return True
            else:
                self.print_failure(f"{name} failed")
                if result.stderr:
                    print(f"{Color.FAIL}Error output:{Color.ENDC}")
                    print(result.stderr)
                if result.stdout:
                    print(f"{Color.FAIL}Standard output:{Color.ENDC}")
                    print(result.stdout)
                return False

        except Exception as e:
            self.print_failure(f"{name} failed with exception: {e}")
            return False

    def run_linters(self) -> bool:
        """Run code linters."""
        self.print_header("LINTERS")

        # Ruff
        ruff_passed = self.run_command(["ruff", "check", "curator/", "tests/"], "Ruff linter")
        self.results["ruff"] = ruff_passed

        # Black
        black_passed = self.run_command(
            ["black", "--check", "curator/", "tests/"], "Black formatter"
        )
        self.results["black"] = black_passed

        # Mypy
        mypy_passed = self.run_command(["mypy", "curator/"], "Mypy type checker")
        self.results["mypy"] = mypy_passed

        return ruff_passed and black_passed and mypy_passed

    def run_unit_tests(self) -> bool:
        """Run unit tests."""
        self.print_header("UNIT TESTS")

        cmd = ["pytest", "tests/unit/", "-v", "--tb=short"]
        if not self.verbose:
            cmd.append("-q")

        unit_passed = self.run_command(cmd, "Unit tests")
        self.results["unit_tests"] = unit_passed

        return unit_passed

    def run_integration_tests(self) -> bool:
        """Run integration tests."""
        self.print_header("INTEGRATION TESTS")

        cmd = ["pytest", "tests/integration/", "-v", "--tb=short"]
        if not self.verbose:
            cmd.append("-q")

        integration_passed = self.run_command(cmd, "Integration tests")
        self.results["integration_tests"] = integration_passed

        return integration_passed

    def run_coverage_tests(self) -> bool:
        """Run tests with coverage."""
        self.print_header("COVERAGE ANALYSIS")

        cmd = [
            "pytest",
            "tests/",
            "--cov=curator",
            "--cov-report=term-missing",
            f"--cov-fail-under={self.coverage_min}",
        ]
        if not self.verbose:
            cmd.append("-q")

        coverage_passed = self.run_command(cmd, "Coverage tests")
        self.results["coverage"] = coverage_passed

        return coverage_passed

    def run_phase_specific_tests(self) -> bool:
        """Run phase-specific tests."""
        if not self.phase:
            return True

        self.print_header(f"PHASE {self.phase} SPECIFIC TESTS")

        phase_tests = {
            "2": ["tests/unit/test_smart_fetcher.py"],
            "3": ["tests/unit/test_cost_tracking.py"],  # Future
        }

        if self.phase not in phase_tests:
            self.print_warning(f"No specific tests defined for Phase {self.phase}")
            return True

        test_files = phase_tests[self.phase]
        all_passed = True

        for test_file in test_files:
            test_path = self.project_root / test_file
            if not test_path.exists():
                self.print_warning(f"Test file not found: {test_file}")
                continue

            cmd = ["pytest", str(test_path), "-v"]
            passed = self.run_command(cmd, f"Phase {self.phase} tests: {test_file}")
            all_passed = all_passed and passed

        self.results[f"phase_{self.phase}"] = all_passed
        return all_passed

    def run_all_tests(self) -> bool:
        """Run all test suites."""
        self.print_header("GITHUB CURATOR - PHASE GATE TEST SUITE")
        print(f"Phase: {self.phase or 'All'}")
        print(f"Strict mode: {self.strict}")
        print(f"Coverage minimum: {self.coverage_min}%")
        print(f"Verbose: {self.verbose}")

        # Run all test suites
        linters_passed = self.run_linters()
        unit_passed = self.run_unit_tests()
        integration_passed = self.run_integration_tests()
        coverage_passed = self.run_coverage_tests()
        phase_passed = self.run_phase_specific_tests()

        # Summary
        self.print_header("TEST SUMMARY")

        all_passed = (
            linters_passed
            and unit_passed
            and integration_passed
            and coverage_passed
            and phase_passed
        )

        for name, passed in self.results.items():
            if passed:
                self.print_success(f"{name}: PASSED")
            else:
                self.print_failure(f"{name}: FAILED")

        print()
        if all_passed:
            self.print_success("ALL TESTS PASSED - PHASE GATE CLEARED ✓")
            return True
        else:
            self.print_failure("SOME TESTS FAILED - PHASE GATE BLOCKED ✗")
            return False

    def run(self) -> int:
        """Run phase gate tests and return exit code."""
        try:
            success = self.run_all_tests()
            return 0 if success else 1
        except KeyboardInterrupt:
            self.print_warning("\nTests interrupted by user")
            return 130
        except Exception as e:
            self.print_failure(f"Unexpected error: {e}")
            return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run phase gate tests for GitHub Curator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_phase_gate_tests.py --phase 2
  python scripts/run_phase_gate_tests.py --strict --coverage-min 80
  python scripts/run_phase_gate_tests.py --verbose
        """,
    )

    parser.add_argument("--phase", type=str, help="Phase number to test (e.g., 2 for Phase 2)")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Strict mode: fail on warnings",
    )
    parser.add_argument(
        "--coverage-min",
        type=int,
        default=70,
        help="Minimum coverage percentage required (default: 70)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    runner = PhaseGateRunner(
        phase=args.phase,
        strict=args.strict,
        coverage_min=args.coverage_min,
        verbose=args.verbose,
    )

    sys.exit(runner.run())


if __name__ == "__main__":
    main()
