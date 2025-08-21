# PowerShell script for d365fo-client Python package
# Use this with './make.ps1 <target>' on Windows PowerShell

param(
    [Parameter(Position=0)]
    [string]$Target = "help"
)

function Show-Help {
    Write-Host "Available targets:" -ForegroundColor Cyan
    Write-Host "  help                Show this help message" -ForegroundColor Gray
    Write-Host "  dev-setup          Set up development environment" -ForegroundColor Gray
    Write-Host "  install            Install package dependencies" -ForegroundColor Gray
    Write-Host "  install-dev        Install package with development dependencies" -ForegroundColor Gray
    Write-Host "  format             Format code with black and isort" -ForegroundColor Gray
    Write-Host "  format-check       Check code formatting without making changes" -ForegroundColor Gray
    Write-Host "  lint               Run linting with ruff" -ForegroundColor Gray
    Write-Host "  lint-fix           Run linting with automatic fixes" -ForegroundColor Gray
    Write-Host "  type-check         Run type checking with mypy" -ForegroundColor Gray
    Write-Host "  quality-check      Run all code quality checks" -ForegroundColor Gray
    Write-Host "  test               Run tests" -ForegroundColor Gray
    Write-Host "  test-unit          Run unit tests only" -ForegroundColor Gray
    Write-Host "  test-integration   Run integration tests only" -ForegroundColor Gray
    Write-Host "  test-verbose       Run tests with verbose output" -ForegroundColor Gray
    Write-Host "  test-coverage      Run tests with coverage report" -ForegroundColor Gray
    Write-Host "  clean              Clean build artifacts" -ForegroundColor Gray
    Write-Host "  build              Build package" -ForegroundColor Gray
    Write-Host "  publish-test       Publish to Test PyPI" -ForegroundColor Gray
    Write-Host "  publish            Publish to PyPI" -ForegroundColor Gray
    Write-Host "  run                Run the application" -ForegroundColor Gray
    Write-Host "  shell              Open Python shell with package installed" -ForegroundColor Gray
    Write-Host "  pre-commit-install Install pre-commit hooks" -ForegroundColor Gray
    Write-Host "  pre-commit         Run pre-commit hooks on all files" -ForegroundColor Gray
    Write-Host "  all                Run quality checks, tests, and build" -ForegroundColor Gray
    Write-Host "  ci                 Run CI pipeline" -ForegroundColor Gray
    Write-Host "  security-check     Run security checks" -ForegroundColor Gray
    Write-Host "  info               Show environment information" -ForegroundColor Gray
    Write-Host "  dev                Quick development check" -ForegroundColor Gray
}

function Invoke-DevSetup {
    Write-Host "Setting up development environment..." -ForegroundColor Green
    uv sync
    uv add --dev pytest black isort mypy ruff pre-commit pytest-cov pip-audit
    Write-Host "Development environment setup complete!" -ForegroundColor Green
}

function Invoke-Install {
    uv sync
}

function Invoke-InstallDev {
    uv sync --dev
}

function Invoke-Format {
    Write-Host "Formatting code..." -ForegroundColor Yellow
    uv run black .
    uv run isort .
    Write-Host "Code formatting complete!" -ForegroundColor Green
}

function Invoke-FormatCheck {
    Write-Host "Checking code formatting..." -ForegroundColor Yellow
    uv run black --check .
    uv run isort --check-only .
}

function Invoke-Lint {
    uv run ruff check .
}

function Invoke-LintFix {
    uv run ruff check --fix .
}

function Invoke-TypeCheck {
    uv run mypy src/
}

function Invoke-QualityCheck {
    Write-Host "Running all code quality checks..." -ForegroundColor Yellow
    Invoke-FormatCheck
    Invoke-Lint
    Invoke-TypeCheck
}

function Invoke-Test {
    uv run pytest
}

function Invoke-TestUnit {
    uv run pytest tests/unit
}

function Invoke-TestIntegration {
    uv run pytest tests/integration
}

function Invoke-TestVerbose {
    uv run pytest -v
}

function Invoke-TestCoverage {
    uv run pytest --cov=d365fo_client --cov-report=html --cov-report=term
}

function Invoke-Clean {
    Write-Host "Cleaning build artifacts..." -ForegroundColor Yellow
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    Get-ChildItem -Recurse -Directory -Name "__pycache__" | Remove-Item -Recurse -Force
    Get-ChildItem -Recurse -Directory -Name ".pytest_cache" | Remove-Item -Recurse -Force
    Get-ChildItem -Recurse -Directory -Name ".mypy_cache" | Remove-Item -Recurse -Force
    Get-ChildItem -Recurse -Name "*.pyc" | Remove-Item -Force
    Get-ChildItem -Recurse -Name "*.egg-info" | Remove-Item -Recurse -Force
    Write-Host "Clean complete!" -ForegroundColor Green
}

function Invoke-Build {
    Invoke-Clean
    uv build
}

function Invoke-PublishTest {
    Invoke-Build
    uv publish --repository testpypi
}

function Invoke-Publish {
    Invoke-Build
    uv publish
}

function Invoke-Run {
    uv run d365fo-client
}

function Invoke-Shell {
    uv run python
}

function Invoke-PreCommitInstall {
    uv run pre-commit install
}

function Invoke-PreCommit {
    uv run pre-commit run --all-files
}

function Invoke-All {
    Write-Host "Running comprehensive checks..." -ForegroundColor Cyan
    Invoke-QualityCheck
    Invoke-Test
    Invoke-Build
}

function Invoke-CI {
    Write-Host "Running CI pipeline..." -ForegroundColor Cyan
    Invoke-InstallDev
    Invoke-QualityCheck
    Invoke-Test
}

function Invoke-SecurityCheck {
    uv run pip-audit
}

function Show-Info {
    Write-Host "Python version:" -ForegroundColor Cyan
    uv run python --version
    Write-Host "`nPackage version:" -ForegroundColor Cyan
    uv run python -c "import d365fo_client; print(d365fo_client.__version__)"
    Write-Host "`nInstalled packages:" -ForegroundColor Cyan
    uv pip list
}

function Invoke-Dev {
    Write-Host "Running quick development check..." -ForegroundColor Cyan
    Invoke-Format
    Invoke-Lint
    Invoke-TypeCheck
    Invoke-Test
}

# Main switch statement
switch ($Target.ToLower()) {
    "help" { Show-Help }
    "dev-setup" { Invoke-DevSetup }
    "install" { Invoke-Install }
    "install-dev" { Invoke-InstallDev }
    "format" { Invoke-Format }
    "format-check" { Invoke-FormatCheck }
    "lint" { Invoke-Lint }
    "lint-fix" { Invoke-LintFix }
    "type-check" { Invoke-TypeCheck }
    "quality-check" { Invoke-QualityCheck }
    "test" { Invoke-Test }
    "test-unit" { Invoke-TestUnit }
    "test-integration" { Invoke-TestIntegration }
    "test-verbose" { Invoke-TestVerbose }
    "test-coverage" { Invoke-TestCoverage }
    "clean" { Invoke-Clean }
    "build" { Invoke-Build }
    "publish-test" { Invoke-PublishTest }
    "publish" { Invoke-Publish }
    "run" { Invoke-Run }
    "shell" { Invoke-Shell }
    "pre-commit-install" { Invoke-PreCommitInstall }
    "pre-commit" { Invoke-PreCommit }
    "all" { Invoke-All }
    "ci" { Invoke-CI }
    "security-check" { Invoke-SecurityCheck }
    "info" { Show-Info }
    "dev" { Invoke-Dev }
    default {
        Write-Host "Unknown target: $Target" -ForegroundColor Red
        Show-Help
    }
}