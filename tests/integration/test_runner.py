"""Test runner script for integration tests.

This script provides an easy way to run integration tests at different levels.
It handles environment setup and provides clear output about test execution.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def setup_environment(test_level: str, verbose: bool = False):
    """Setup environment variables for integration testing."""
    # Load .env file if it exists
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key and not os.getenv(
                            key
                        ):  # Don't override existing env vars
                            os.environ[key] = value
            if verbose:
                print(f"📄 Loaded environment variables from {env_file}")
        except Exception as e:
            if verbose:
                print(f"⚠️  Could not load .env file: {e}")

    os.environ["INTEGRATION_TEST_LEVEL"] = test_level

    # Set up test environment URLs if not already set
    if test_level in ["sandbox", "all"] and not os.getenv("D365FO_SANDBOX_BASE_URL"):
        print("⚠️  D365FO_SANDBOX_BASE_URL not set. Sandbox tests will be skipped.")

    if test_level in ["live", "all"] and not os.getenv("D365FO_LIVE_BASE_URL"):
        print("⚠️  D365FO_LIVE_BASE_URL not set. Live tests will be skipped.")

    if verbose:
        print(f"📋 Integration test level: {test_level}")
        print(f"📁 Test directory: {Path(__file__).parent}")


def run_tests(
    test_level: str,
    specific_test: str = None,
    verbose: bool = False,
    coverage: bool = False,
    markers: str = None,
):
    """Run integration tests with specified parameters."""

    setup_environment(test_level, verbose)

    # Build pytest command
    # Check if we're running under uv and use the appropriate command
    import shutil

    if shutil.which("uv"):
        # Try uv run pytest first
        cmd = ["uv", "run", "pytest"]
    else:
        # Fallback to traditional python -m pytest
        cmd = ["python", "-m", "pytest"]

    # Add test directory and filtering based on test level
    test_dir = Path(__file__).parent
    if specific_test:
        cmd.append(str(test_dir / specific_test))
    else:
        # Filter tests based on level to avoid running incompatible tests
        if test_level == "sandbox":
            # Include all sandbox test files currently in integration directory
            cmd.extend(
                [
                    str(test_dir / "test_sandbox.py"),
                    str(test_dir / "test_sandbox_crud.py"),
                    str(test_dir / "test_sandbox_metadata.py"),
                    str(test_dir / "test_sandbox_performance.py"),
                    str(test_dir / "test_sandbox_error_handling.py"),
                ]
            )
        elif test_level == "live":
            # Live tests to be implemented - for now run sandbox tests
            print("⚠️  Live tests not yet implemented. Running sandbox tests instead.")
            cmd.extend(
                [
                    str(test_dir / "test_sandbox.py"),
                    str(test_dir / "test_sandbox_crud.py"),
                    str(test_dir / "test_sandbox_metadata.py"),
                    str(test_dir / "test_sandbox_performance.py"),
                    str(test_dir / "test_sandbox_error_handling.py"),
                ]
            )
        else:
            # For 'all' level, run everything in integration directory
            cmd.append(str(test_dir))

    # Add pytest options
    cmd.extend(
        [
            "-v" if verbose else "-q",
            "--tb=short",
            "-ra",  # Show summary of all test results
        ]
    )

    # Add markers
    if markers:
        cmd.extend(["-m", markers])

    # Add coverage if requested
    if coverage:
        cmd.extend(
            ["--cov=d365fo_client", "--cov-report=html", "--cov-report=term-missing"]
        )

    if verbose:
        print(f"🚀 Running command: {' '.join(cmd)}")

    # Run tests
    result = subprocess.run(cmd, cwd=test_dir.parent.parent)
    return result.returncode


def check_dependencies():
    """Check if required test dependencies are installed."""
    required_packages = ["pytest", "pytest-asyncio", "aiohttp"]
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Install them with: uv add --dev " + " ".join(missing_packages))
        return False

    return True


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(
        description="Run D365 F&O Client Integration Tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Test Levels:
  sandbox  - Run sandbox tests (requires D365 F&O test environment)
  live     - Run live tests (currently runs sandbox tests - live tests TBD)
  all      - Run all integration tests in the directory

Available Test Files:
  test_sandbox.py                    - Core connection and version tests
  test_sandbox_crud.py               - CRUD operations and data validation
  test_sandbox_metadata.py           - Metadata API and entity discovery
  test_sandbox_performance.py        - Performance benchmarking
  test_sandbox_error_handling.py     - Error scenarios and resilience

Examples:
  # Run all sandbox tests
  python test_runner.py sandbox

  # Run with verbose output
  python test_runner.py sandbox --verbose

  # Run specific test category
  python test_runner.py sandbox --test test_sandbox_crud.py

  # Run with coverage report
  python test_runner.py sandbox --coverage

  # Run performance tests only
  python test_runner.py sandbox --markers "performance"

  # Skip slow tests
  python test_runner.py sandbox --markers "not slow"

Required Environment Variables:
  D365FO_SANDBOX_BASE_URL    - URL for sandbox environment (required)

Optional Environment Variables:
  D365FO_CLIENT_ID           - Azure AD client ID (if not using default credentials)
  D365FO_CLIENT_SECRET       - Azure AD client secret
  D365FO_TENANT_ID           - Azure AD tenant ID

Note: Unit tests for version methods are now in tests/unit/ directory.
        """,
    )

    parser.add_argument(
        "level",
        choices=["sandbox", "live", "all"],
        help="Integration test level to run",
    )

    parser.add_argument(
        "--test",
        "-t",
        help="Specific test file to run (e.g., test_sandbox_crud.py, test_sandbox_metadata.py)",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    parser.add_argument(
        "--coverage", "-c", action="store_true", help="Generate coverage report"
    )

    parser.add_argument(
        "--markers", "-m", help="Run tests matching specific pytest markers"
    )

    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check if required dependencies are installed",
    )

    args = parser.parse_args()

    if args.check_deps:
        if check_dependencies():
            print("✅ All required dependencies are installed")
            return 0
        else:
            return 1

    # Check dependencies before running tests
    if not check_dependencies():
        return 1

    print(f"🧪 Running D365 F&O Integration Tests - Level: {args.level}")
    print("=" * 60)

    return_code = run_tests(
        test_level=args.level,
        specific_test=args.test,
        verbose=args.verbose,
        coverage=args.coverage,
        markers=args.markers,
    )

    if return_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code: {return_code}")

    return return_code


if __name__ == "__main__":
    sys.exit(main())
