.PHONY: help install install-dev test lint format clean build

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install:  ## Install package in development mode
	pip install -e .

install-dev:  ## Install package with development dependencies
	pip install -e ".[dev]"

test:  ## Run all tests with coverage
	pytest

test-verbose:  ## Run tests with verbose output
	pytest -v

test-unit:  ## Run unit tests only
	pytest tests/unit/ -v

test-integration:  ## Run integration tests only
	pytest tests/integration/ -v

test-coverage:  ## Run tests with detailed coverage report
	pytest --cov=curator --cov-report=html --cov-report=term-missing

test-phase-gate:  ## Run phase gate tests (use PHASE=N for specific phase)
	python scripts/run_phase_gate_tests.py $(if $(PHASE),--phase $(PHASE),)

test-phase-gate-strict:  ## Run phase gate tests in strict mode
	python scripts/run_phase_gate_tests.py --strict --coverage-min 80

lint:  ## Run code linters
	ruff check curator/ tests/
	mypy curator/

format:  ## Format code with black and ruff
	black curator/ tests/
	ruff check --fix curator/ tests/

check:  ## Run all checks (lint + test)
	@make lint
	@make test

clean:  ## Remove build artifacts and cache
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

build:  ## Build distribution packages
	python -m build

setup:  ## Verify environment setup
	python -m curator setup

curate:  ## Run example curation (THEME="your theme")
	python -m curator curate "$(THEME)" --limit 10

validate:  ## Validate configuration
	python -m curator validate-config

quickstart:  ## Run quickstart example
	python examples/quickstart.py
