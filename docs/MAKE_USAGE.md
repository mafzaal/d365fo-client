# Make Files Usage Guide

This project includes three different "make" implementations to support various development environments:

## 1. Makefile (Unix/Linux/macOS)
For Unix-like systems with `make` installed:
```bash
make help              # Show available targets
make dev-setup         # Set up development environment
make test              # Run tests
make dev               # Quick development check (format + lint + test)
make build             # Build package
```

## 2. make.bat (Windows Command Prompt)
For Windows Command Prompt or PowerShell:
```cmd
make.bat help          # Show available targets
make.bat dev-setup     # Set up development environment
make.bat test          # Run tests
make.bat dev           # Quick development check
make.bat build         # Build package
```

## 3. make.ps1 (Windows PowerShell)
For Windows PowerShell with enhanced formatting:
```powershell
.\make.ps1 help        # Show available targets
.\make.ps1 dev-setup   # Set up development environment
.\make.ps1 test        # Run tests
.\make.ps1 dev         # Quick development check
.\make.ps1 build       # Build package
```

## Common Development Workflow

### Initial Setup
```bash
# Choose one based on your system:
make dev-setup         # Unix/Linux/macOS
make.bat dev-setup     # Windows CMD
.\make.ps1 dev-setup   # Windows PowerShell
```

### Daily Development
```bash
# Quick development check (format, lint, type-check, test)
make dev               # Unix/Linux/macOS
make.bat dev           # Windows CMD
.\make.ps1 dev         # Windows PowerShell
```

### Before Committing
```bash
# Run comprehensive checks
make quality-check     # Unix/Linux/macOS
make.bat quality-check # Windows CMD
.\make.ps1 quality-check # Windows PowerShell
```

### Building and Publishing
```bash
# Build package
make build             # Unix/Linux/macOS
make.bat build         # Windows CMD
.\make.ps1 build       # Windows PowerShell

# Publish to Test PyPI
make publish-test      # Unix/Linux/macOS
make.bat publish-test  # Windows CMD
.\make.ps1 publish-test # Windows PowerShell

# Publish to PyPI
make publish           # Unix/Linux/macOS
make.bat publish       # Windows CMD
.\make.ps1 publish     # Windows PowerShell
```

## Available Targets

| Target | Description |
|--------|-------------|
| `help` | Show available targets |
| `dev-setup` | Set up development environment |
| `install` | Install package dependencies |
| `install-dev` | Install with development dependencies |
| `format` | Format code with black and isort |
| `format-check` | Check formatting without changes |
| `lint` | Run linting with ruff |
| `lint-fix` | Run linting with automatic fixes |
| `type-check` | Run type checking with mypy |
| `quality-check` | Run all code quality checks |
| `test` | Run tests |
| `test-verbose` | Run tests with verbose output |
| `test-coverage` | Run tests with coverage report |
| `clean` | Clean build artifacts |
| `build` | Build package |
| `publish-test` | Publish to Test PyPI |
| `publish` | Publish to PyPI |
| `run` | Run the application |
| `shell` | Open Python shell |
| `pre-commit-install` | Install pre-commit hooks |
| `pre-commit` | Run pre-commit hooks |
| `all` | Run quality checks, tests, and build |
| `ci` | Run CI pipeline |
| `security-check` | Run security checks |
| `info` | Show environment information |
| `dev` | Quick development check |

## Recommended Workflow

1. **Setup**: Run `dev-setup` once after cloning
2. **Development**: Use `dev` for quick checks during development
3. **Before commit**: Run `quality-check` to ensure code quality
4. **Release**: Use `build` and `publish` for releases
5. **CI/CD**: Use `ci` target for automated pipelines