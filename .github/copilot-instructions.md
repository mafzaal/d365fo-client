# Copilot Instructions for d365fo-client Python Package

## Project Overview
This is a Python package project named `d365fo-client` that uses `uv` for dependency management and will be published to PyPI.org. The project follows modern Python packaging standards with `pyproject.toml` configuration.

## Development Environment
- **Package Manager**: `uv` (for fast Python package management)
- **Python Version**: >=3.13
- **Build Backend**: `hatchling` (default for uv projects)
- **Distribution**: PyPI.org

## Project Structure Guidelines
```
d365fo-client/
├── src/
│   └── d365fo_client/
│       ├── __init__.py
│       ├── main.py
│       └── ...
├── tests/
│   ├── __init__.py
│   └── test_*.py
├── docs/
├── pyproject.toml
├── README.md
├── LICENSE
├── .gitignore
└── CHANGELOG.md
```

## Key Development Practices

### 1. Package Management with uv
- Use `uv add <package>` to add dependencies
- Use `uv add --dev <package>` for development dependencies
- Use `uv sync` to install dependencies from lockfile
- Use `uv run <command>` to run commands in the project environment
- Use `uv build` to build distribution packages
- Use `uv publish` to publish to PyPI

### 2. Code Organization
- Place all source code in `src/d365fo_client/` directory
- Use proper `__init__.py` files for package initialization
- Export main functionality through `__init__.py`
- Follow PEP 8 style guidelines
- Use type hints for all functions and methods

### 3. Dependencies and Requirements
- Add all runtime dependencies to `pyproject.toml` under `[project]` dependencies
- Add development dependencies using `uv add --dev`
- Pin exact versions for reproducible builds
- Keep dependencies minimal and well-justified

### 4. Testing
- Use `pytest` as the testing framework
- Place tests in `tests/` directory
- Name test files with `test_` prefix
- Aim for high test coverage (>90%)
- Run tests with `uv run pytest`

### 5. Documentation
- Store all documentation files in the `docs/` folder
- Maintain comprehensive README.md with usage examples
- Use docstrings for all public functions and classes
- Follow Google or NumPy docstring format
- Place API documentation, guides, and tutorials in `docs/`
- Consider using Sphinx for API documentation with output to `docs/`

### 6. Version Management
- Follow semantic versioning (MAJOR.MINOR.PATCH)
- Update version in `pyproject.toml` before releases
- Maintain CHANGELOG.md with release notes
- Tag releases in git with version numbers

## pyproject.toml Configuration Guidelines

### Essential sections to include:
```toml
[project]
name = "d365fo-client"
version = "x.y.z"
description = "Microsot Dynamics 365 Finance & Operations client"
readme = "README.md"
license = { text = "MIT" }
authors = [{ name = "Muhammad Afzaal", email = "mo@thedataguy.pro" }]
requires-python = ">=3.13"
dependencies = []
keywords = ["keyword1", "keyword2"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.13",
]

[project.urls]
Homepage = "https://github.com/mafzaal/d365fo-client"
Repository = "https://github.com/mafzaal/d365fo-client"
Documentation = "https://d365fo-client.readthedocs.io"
Issues = "https://github.com/mafzaal/d365fo-client/issues"

[project.scripts]
d365fo-client = "d365fo_client.main:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build_meta"

[tool.hatch.build.targets.sdist]
include = ["src/d365fo_client"]

[tool.hatch.build.targets.wheel]
packages = ["src/d365fo_client"]
```

## Development Workflow

### Setting up development environment:
1. `uv sync` - Install dependencies
2. `uv add --dev pytest black isort mypy` - Add development tools
3. `uv run pytest` - Run tests

### Before committing:
1. `uv run black .` - Format code
2. `uv run isort .` - Sort imports
3. `uv run mypy src/` - Type checking
4. `uv run pytest` - Run tests

### Publishing workflow:
1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. `uv build` - Build distribution packages
4. `uv publish` - Publish to PyPI (requires API token)

## Code Quality Standards
- Use Black for code formatting
- Use isort for import sorting
- Use mypy for static type checking
- Use ruff for fast linting
- Maintain test coverage above 90%
- All public APIs must have type hints and docstrings

## Security Considerations
- Never commit API keys or secrets
- Use environment variables for configuration
- Validate all user inputs
- Follow security best practices for package distribution

## Publishing Checklist
Before publishing to PyPI:
- [ ] Version number updated
- [ ] CHANGELOG.md updated
- [ ] All tests passing
- [ ] Documentation updated
- [ ] License file included
- [ ] README.md comprehensive
- [ ] Clean git working directory
- [ ] Tagged release in git

## Common Commands
- `uv add package-name` - Add dependency
- `uv add --dev package-name` - Add dev dependency
- `uv sync` - Install/sync dependencies
- `uv run command` - Run command in project environment
- `uv build` - Build distribution packages
- `uv publish` - Publish to PyPI
- `uv run pytest` - Run tests
- `uv run black .` - Format code

## When creating new features:
1. Create feature branch
2. Add tests first (TDD approach)
3. Implement feature with proper type hints
4. Update documentation
5. Ensure all quality checks pass
6. Create pull request

## Error Handling
- Use specific exception types
- Provide clear error messages
- Log errors appropriately
- Handle edge cases gracefully
- Document expected exceptions in docstrings