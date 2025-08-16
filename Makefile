# Makefile for d365fo-client Python package
# Use this with 'make <target>' on Unix-like systems or 'mingw32-make <target>' on Windows

.PHONY: help install install-dev test test-verbose lint format type-check quality-check clean build publish dev-setup run docs-build docs-serve pre-commit all

# Default target
help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development setup
dev-setup: ## Set up development environment
	uv sync
	uv add --dev pytest black isort mypy ruff pre-commit
	@echo "Development environment setup complete!"

install: ## Install package dependencies
	uv sync

install-dev: ## Install package with development dependencies
	uv sync --dev

# Code quality
format: ## Format code with black and isort
	uv run black .
	uv run isort .
	@echo "Code formatting complete!"

format-check: ## Check code formatting without making changes
	uv run black --check .
	uv run isort --check-only .

lint: ## Run linting with ruff
	uv run ruff check .

lint-fix: ## Run linting with automatic fixes
	uv run ruff check --fix .

type-check: ## Run type checking with mypy
	uv run mypy src/

quality-check: format-check lint type-check ## Run all code quality checks

# Testing
test: ## Run tests
	uv run pytest

test-verbose: ## Run tests with verbose output
	uv run pytest -v

test-coverage: ## Run tests with coverage report
	uv run pytest --cov=d365fo_client --cov-report=html --cov-report=term

test-watch: ## Run tests in watch mode (requires pytest-watch)
	uv run ptw

# Building and publishing
clean: ## Clean build artifacts
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	rm -rf src/*.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
	find . -type d -name .pytest_cache -delete
	find . -type d -name .mypy_cache -delete

build: clean ## Build package
	uv build

publish-test: build ## Publish to Test PyPI
	uv publish --repository testpypi

publish: build ## Publish to PyPI
	uv publish

# Development commands
run: ## Run the application
	uv run d365fo-client

shell: ## Open Python shell with package installed
	uv run python

# Pre-commit hooks
pre-commit-install: ## Install pre-commit hooks
	uv run pre-commit install

pre-commit: ## Run pre-commit hooks on all files
	uv run pre-commit run --all-files

# Documentation (if using sphinx)
docs-build: ## Build documentation
	@echo "Documentation build not configured yet"

docs-serve: ## Serve documentation locally
	@echo "Documentation serve not configured yet"

# Comprehensive targets
all: quality-check test build ## Run quality checks, tests, and build

ci: install-dev quality-check test ## Run CI pipeline (install, quality checks, tests)

release-patch: ## Bump patch version and create release
	@echo "Release automation not implemented yet"

release-minor: ## Bump minor version and create release
	@echo "Release automation not implemented yet"

release-major: ## Bump major version and create release
	@echo "Release automation not implemented yet"

# Security
security-check: ## Run security checks
	uv run pip-audit

# Environment info
info: ## Show environment information
	@echo "Python version:"
	uv run python --version
	@echo "\nPackage version:"
	uv run python -c "import d365fo_client; print(d365fo_client.__version__)"
	@echo "\nInstalled packages:"
	uv pip list

# Quick development workflow
dev: format lint type-check test ## Quick development check (format, lint, type-check, test)

# Help ensure targets are not confused with files
.SUFFIXES: