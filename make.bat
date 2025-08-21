@echo off
REM Batch file for d365fo-client Python package (Windows equivalent of Makefile)
REM Use this with 'make.bat <target>' on Windows

if "%1"=="help" goto help
if "%1"=="dev-setup" goto dev-setup
if "%1"=="install" goto install
if "%1"=="install-dev" goto install-dev
if "%1"=="format" goto format
if "%1"=="format-check" goto format-check
if "%1"=="lint" goto lint
if "%1"=="lint-fix" goto lint-fix
if "%1"=="type-check" goto type-check
if "%1"=="quality-check" goto quality-check
if "%1"=="test" goto test
if "%1"=="test-unit" goto test-unit
if "%1"=="test-integration" goto test-integration
if "%1"=="test-verbose" goto test-verbose
if "%1"=="test-coverage" goto test-coverage
if "%1"=="clean" goto clean
if "%1"=="build" goto build
if "%1"=="publish-test" goto publish-test
if "%1"=="publish" goto publish
if "%1"=="run" goto run
if "%1"=="shell" goto shell
if "%1"=="pre-commit-install" goto pre-commit-install
if "%1"=="pre-commit" goto pre-commit
if "%1"=="all" goto all
if "%1"=="ci" goto ci
if "%1"=="security-check" goto security-check
if "%1"=="info" goto info
if "%1"=="dev" goto dev

if "%1"=="" goto help

echo Unknown target: %1
goto help

:help
echo Available targets:
echo   help                Show this help message
echo   dev-setup          Set up development environment
echo   install            Install package dependencies
echo   install-dev        Install package with development dependencies
echo   format             Format code with black and isort
echo   format-check       Check code formatting without making changes
echo   lint               Run linting with ruff
echo   lint-fix           Run linting with automatic fixes
echo   type-check         Run type checking with mypy
echo   quality-check      Run all code quality checks
echo   test               Run tests
echo   test-unit          Run unit tests only
echo   test-integration   Run integration tests only
echo   test-verbose       Run tests with verbose output
echo   test-coverage      Run tests with coverage report
echo   clean              Clean build artifacts
echo   build              Build package
echo   publish-test       Publish to Test PyPI
echo   publish            Publish to PyPI
echo   run                Run the application
echo   shell              Open Python shell with package installed
echo   pre-commit-install Install pre-commit hooks
echo   pre-commit         Run pre-commit hooks on all files
echo   all                Run quality checks, tests, and build
echo   ci                 Run CI pipeline
echo   security-check     Run security checks
echo   info               Show environment information
echo   dev                Quick development check
goto end

:dev-setup
echo Setting up development environment...
uv sync
uv add --dev pytest black isort mypy ruff pre-commit pytest-cov pip-audit
echo Development environment setup complete!
goto end

:install
uv sync
goto end

:install-dev
uv sync --dev
goto end

:format
echo Formatting code...
uv run black .
uv run isort .
echo Code formatting complete!
goto end

:format-check
echo Checking code formatting...
uv run black --check .
uv run isort --check-only .
goto end

:lint
uv run ruff check .
goto end

:lint-fix
uv run ruff check --fix .
goto end

:type-check
uv run mypy src/
goto end

:quality-check
echo Running all code quality checks...
call %0 format-check
call %0 lint
call %0 type-check
goto end

:test
uv run pytest
goto end

:test-unit
uv run pytest tests/unit
goto end

:test-integration
uv run pytest tests/integration
goto end

:test-verbose
uv run pytest -v
goto end

:test-coverage
uv run pytest --cov=d365fo_client --cov-report=html --cov-report=term
goto end

:clean
echo Cleaning build artifacts...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist *.egg-info rmdir /s /q *.egg-info
if exist src\*.egg-info rmdir /s /q src\*.egg-info
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
for /d /r . %%d in (.pytest_cache) do @if exist "%%d" rmdir /s /q "%%d"
for /d /r . %%d in (.mypy_cache) do @if exist "%%d" rmdir /s /q "%%d"
del /s /q *.pyc 2>nul
echo Clean complete!
goto end

:build
call %0 clean
uv build
goto end

:publish-test
call %0 build
uv publish --repository testpypi
goto end

:publish
call %0 build
uv publish
goto end

:run
uv run d365fo-client
goto end

:shell
uv run python
goto end

:pre-commit-install
uv run pre-commit install
goto end

:pre-commit
uv run pre-commit run --all-files
goto end

:all
echo Running comprehensive checks...
call %0 quality-check
call %0 test
call %0 build
goto end

:ci
echo Running CI pipeline...
call %0 install-dev
call %0 quality-check
call %0 test
goto end

:security-check
uv run pip-audit
goto end

:info
echo Python version:
uv run python --version
echo.
echo Package version:
uv run python -c "import d365fo_client; print(d365fo_client.__version__)"
echo.
echo Installed packages:
uv pip list
goto end

:dev
echo Running quick development check...
call %0 format
call %0 lint
call %0 type-check
call %0 test
goto end

:end