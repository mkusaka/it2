.PHONY: help install build test test-cov lint lint-fix format format-check mypy check clean publish publish-test version-patch version-minor version-major patch minor major

# Default target - show help
.DEFAULT_GOAL := help

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development setup
install: ## Install all dependencies including dev
	uv sync --all-extras --dev

# Building
build: ## Build the package
	uv build

# Testing
test: ## Run tests
	uv run pytest

test-cov: ## Run tests with coverage report
	uv run pytest --cov=it2 --cov-report=xml --cov-report=term

# Code quality
lint: ## Run linting checks with ruff
	uv run ruff check src tests

lint-fix: ## Run linting with auto-fix
	uv run ruff check --fix src tests

format: ## Format code with black and ruff
	uv run black .
	uv run ruff check --fix .

format-check: ## Check code formatting without changes
	uv run black --check .

mypy: ## Run type checking with mypy
	uv run mypy src

check: lint mypy format-check test ## Run all quality checks

# Versioning
version-patch: ## Bump patch version (0.0.X)
	@uv run python scripts/bump_version.py patch

version-minor: ## Bump minor version (0.X.0)
	@uv run python scripts/bump_version.py minor

version-major: ## Bump major version (X.0.0)
	@uv run python scripts/bump_version.py major

# Version aliases for convenience
patch: version-patch ## Alias for version-patch

minor: version-minor ## Alias for version-minor

major: version-major ## Alias for version-major

# Publishing
publish: clean build ## Build and publish to PyPI
	uv run twine upload dist/*

publish-test: clean build ## Build and publish to TestPyPI
	uv run twine upload --repository testpypi dist/*

# Cleanup
clean: ## Remove build artifacts and cache files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# CI/CD aliases
ci-ready: check ## Alias for check (backwards compatibility)