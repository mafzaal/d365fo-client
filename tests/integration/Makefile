# Makefile for D365 F&O Client Integration Tests

.PHONY: help setup test-mock test-sandbox test-live test-all clean coverage deps-check

# Default target
help:
	@echo "D365 F&O Client Integration Testing"
	@echo "=================================="
	@echo ""
	@echo "Available targets:"
	@echo "  setup        - Setup integration testing environment"
	@echo "  deps-check   - Check if dependencies are installed"
	@echo "  test-mock    - Run mock server tests"
	@echo "  test-sandbox - Run sandbox environment tests"
	@echo "  test-live    - Run live environment tests"
	@echo "  test-all     - Run all integration tests"
	@echo "  coverage     - Run tests with coverage report"
	@echo "  clean        - Clean up test artifacts"
	@echo "  help         - Show this help message"
	@echo ""
	@echo "Examples:"
	@echo "  make setup"
	@echo "  make test-mock"
	@echo "  make test-sandbox"
	@echo "  make coverage"

# Setup integration testing environment
setup:
	@echo "🔧 Setting up integration testing environment..."
	@python tests/integration/setup.py

# Check dependencies
deps-check:
	@echo "🔍 Checking dependencies..."
	@python tests/integration/test_runner.py mock --check-deps

# Run mock server tests
test-mock:
	@echo "🧪 Running mock server tests..."
	@python tests/integration/test_runner.py mock

# Run sandbox tests
test-sandbox:
	@echo "🧪 Running sandbox tests..."
	@python tests/integration/test_runner.py sandbox

# Run live environment tests
test-live:
	@echo "🧪 Running live environment tests..."
	@python tests/integration/test_runner.py live

# Run all integration tests
test-all:
	@echo "🧪 Running all integration tests..."
	@python tests/integration/test_runner.py all

# Run tests with coverage
coverage:
	@echo "📊 Running tests with coverage..."
	@python tests/integration/test_runner.py mock --coverage

# Run verbose tests
test-verbose:
	@echo "🧪 Running mock tests with verbose output..."
	@python tests/integration/test_runner.py mock --verbose

# Clean up test artifacts
clean:
	@echo "🧹 Cleaning up test artifacts..."
	@find tests/integration -name "*.pyc" -delete
	@find tests/integration -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@rm -rf tests/integration/.pytest_cache
	@rm -rf htmlcov
	@rm -f .coverage
	@echo "✅ Cleanup complete"

# Advanced targets

# Run specific test file
test-file:
	@if [ -z "$(FILE)" ]; then \
		echo "❌ Please specify FILE=test_file_name.py"; \
		exit 1; \
	fi
	@echo "🧪 Running specific test file: $(FILE)"
	@python tests/integration/test_runner.py mock --test $(FILE)

# Run tests with specific markers
test-markers:
	@if [ -z "$(MARKERS)" ]; then \
		echo "❌ Please specify MARKERS='marker1 and marker2'"; \
		exit 1; \
	fi
	@echo "🧪 Running tests with markers: $(MARKERS)"
	@python tests/integration/test_runner.py mock --markers "$(MARKERS)"

# Performance tests only
test-performance:
	@echo "⚡ Running performance tests..."
	@python tests/integration/test_runner.py mock --markers "performance"

# Quick smoke test
smoke-test:
	@echo "💨 Running smoke test..."
	@python tests/integration/test_runner.py mock --test test_mock_server.py::TestConnectionMockServer::test_connection_success

# Development targets

# Install integration dependencies
install-deps:
	@echo "📦 Installing integration dependencies..."
	@uv add --group integration aiohttp pytest-asyncio pytest-cov httpx

# Start mock server manually (for debugging)
start-mock-server:
	@echo "🚀 Starting mock server on http://localhost:8000"
	@echo "Press Ctrl+C to stop"
	@python -c "import asyncio; from tests.integration.mock_server import D365MockServer; asyncio.run(D365MockServer().start()); input('Press Enter to stop...')"

# Validate test configuration
validate-config:
	@echo "🔍 Validating test configuration..."
	@python -c "from tests.integration import TEST_ENVIRONMENTS; print('✅ Configuration valid')"

# Show test statistics
test-stats:
	@echo "📈 Test Statistics:"
	@find tests/integration -name "test_*.py" -exec wc -l {} + | tail -1 | awk '{print "  Total lines of test code: " $$1}'
	@find tests/integration -name "test_*.py" | wc -l | awk '{print "  Number of test files: " $$1}'
	@grep -r "async def test_" tests/integration --include="*.py" | wc -l | awk '{print "  Number of test functions: " $$1}'

# CI/CD targets

# Target for GitHub Actions
ci-tests:
	@echo "🤖 Running CI tests..."
	@python tests/integration/test_runner.py mock --coverage
	@if [ -n "$$D365FO_SANDBOX_BASE_URL" ]; then \
		echo "🧪 Running sandbox tests in CI..."; \
		python tests/integration/test_runner.py sandbox; \
	else \
		echo "⏭️  Skipping sandbox tests in CI (no environment configured)"; \
	fi

# Target for local development
dev-test:
	@echo "👨‍💻 Running development tests..."
	@python tests/integration/test_runner.py mock --verbose

# Show environment information
env-info:
	@echo "🌍 Environment Information:"
	@echo "  Python version: $$(python --version)"
	@echo "  Working directory: $$(pwd)"
	@echo "  Integration test level: $${INTEGRATION_TEST_LEVEL:-mock}"
	@echo "  Sandbox URL: $${D365FO_SANDBOX_BASE_URL:-not set}"
	@echo "  Live URL: $${D365FO_LIVE_BASE_URL:-not set}"
	@echo "  Azure Client ID: $${D365FO_CLIENT_ID:+set}"
	@if command -v uv >/dev/null 2>&1; then echo "  uv: installed"; else echo "  uv: not installed"; fi