.PHONY: help test lint format mypy ci-ready version-patch version-minor version-major

help:
	@echo "Available commands:"
	@echo "  make test          Run tests"
	@echo "  make lint          Run linting checks"
	@echo "  make format        Format code with black"
	@echo "  make format-check  Check code formatting"
	@echo "  make mypy          Run type checking"
	@echo "  make ci-ready      Run all checks (lint, format-check, mypy, test)"
	@echo "  make version-patch Bump patch version (0.0.X)"
	@echo "  make version-minor Bump minor version (0.X.0)"
	@echo "  make version-major Bump major version (X.0.0)"

test:
	uv run pytest

test-cov:
	uv run pytest --cov=it2 --cov-report=term

lint:
	uv run ruff check .

format:
	uv run black .
	uv run ruff check --fix .

format-check:
	uv run black --check .

mypy:
	uv run mypy src

ci-ready: lint format-check mypy test

version-patch:
	uv run python scripts/bump_version.py patch

version-minor:
	uv run python scripts/bump_version.py minor

version-major:
	uv run python scripts/bump_version.py major