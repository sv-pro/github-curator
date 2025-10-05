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

test:  ## Run tests with coverage
	pytest

test-verbose:  ## Run tests with verbose output
	pytest -v

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
