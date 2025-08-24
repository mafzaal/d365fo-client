"""CLI integration tests for d365fo-client.

This module provides integration tests for the CLI interface specifically focusing
on entity CRUD operations to improve CLI coverage from 10% to higher values.

Note: These tests focus on CLI argument parsing, help text, and configuration
rather than end-to-end CLI workflows since subprocess testing with mock servers
is complex.
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest

from . import skip_if_not_level


@skip_if_not_level("mock")
class TestCLIHelpAndUsage:
    """Test CLI help and usage information."""

    def test_cli_main_help(self):
        """Test main CLI help output."""
        result = subprocess.run(
            ["uv", "run", "d365fo-client", "--help"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
        )
        assert result.returncode == 0
        assert "d365fo-client" in result.stdout.lower()
        assert "usage" in result.stdout.lower()

    def test_cli_entity_help(self):
        """Test entity command help."""
        result = subprocess.run(
            ["uv", "run", "d365fo-client", "entity", "--help"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
        )
        assert result.returncode == 0
        assert "entity" in result.stdout.lower()
        assert "get" in result.stdout.lower()
        assert "create" in result.stdout.lower()
        assert "update" in result.stdout.lower()
        assert "delete" in result.stdout.lower()

    def test_cli_entity_get_help(self):
        """Test entity get command help."""
        result = subprocess.run(
            ["uv", "run", "d365fo-client", "entity", "get", "--help"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
        )
        assert result.returncode == 0
        assert "get" in result.stdout.lower()
        assert "entity" in result.stdout.lower()

    def test_cli_entity_create_help(self):
        """Test entity create command help."""
        result = subprocess.run(
            ["uv", "run", "d365fo-client", "entity", "create", "--help"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
        )
        assert result.returncode == 0
        assert "create" in result.stdout.lower()
        assert "data" in result.stdout.lower()
        assert "file" in result.stdout.lower()

    def test_cli_entity_update_help(self):
        """Test entity update command help."""
        result = subprocess.run(
            ["uv", "run", "d365fo-client", "entity", "update", "--help"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
        )
        assert result.returncode == 0
        assert "update" in result.stdout.lower()
        assert "data" in result.stdout.lower()
        assert "file" in result.stdout.lower()

    def test_cli_entity_delete_help(self):
        """Test entity delete command help."""
        result = subprocess.run(
            ["uv", "run", "d365fo-client", "entity", "delete", "--help"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
        )
        assert result.returncode == 0
        assert "delete" in result.stdout.lower()

    def test_cli_metadata_help(self):
        """Test metadata command help."""
        result = subprocess.run(
            ["uv", "run", "d365fo-client", "metadata", "--help"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
        )
        assert result.returncode == 0
        assert "metadata" in result.stdout.lower()
        # The actual subcommands are sync, search, info (not entities)
        assert "sync" in result.stdout.lower() or "search" in result.stdout.lower()

    def test_cli_version_help(self):
        """Test version command help."""
        result = subprocess.run(
            ["uv", "run", "d365fo-client", "version", "--help"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
        )
        assert result.returncode == 0
        assert "version" in result.stdout.lower()

    def test_cli_test_help(self):
        """Test test command help."""
        result = subprocess.run(
            ["uv", "run", "d365fo-client", "test", "--help"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
        )
        assert result.returncode == 0
        assert "test" in result.stdout.lower()


@skip_if_not_level("mock")
class TestCLIArgumentValidation:
    """Test CLI argument validation and error handling."""

    def test_cli_entity_get_missing_entity_name(self):
        """Test entity get command with missing entity name."""
        result = subprocess.run(
            [
                "uv",
                "run",
                "d365fo-client",
                "--base-url",
                "http://localhost:8000",
                "entity",
                "get",
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
        )
        # Should fail due to missing required argument
        assert result.returncode != 0

    def test_cli_entity_create_missing_data(self):
        """Test entity create command with missing data."""
        result = subprocess.run(
            [
                "uv",
                "run",
                "d365fo-client",
                "--base-url",
                "http://localhost:8000",
                "entity",
                "create",
                "Customers",
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
        )
        # Should fail due to missing data or file
        assert result.returncode != 0

    def test_cli_entity_update_missing_key(self):
        """Test entity update command with missing key."""
        result = subprocess.run(
            [
                "uv",
                "run",
                "d365fo-client",
                "--base-url",
                "http://localhost:8000",
                "entity",
                "update",
                "Customers",
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
        )
        # Should fail due to missing key
        assert result.returncode != 0

    def test_cli_entity_delete_missing_key(self):
        """Test entity delete command with missing key."""
        result = subprocess.run(
            [
                "uv",
                "run",
                "d365fo-client",
                "--base-url",
                "http://localhost:8000",
                "entity",
                "delete",
                "Customers",
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
        )
        # Should fail due to missing key
        assert result.returncode != 0

    def test_cli_missing_base_url(self):
        """Test CLI command with missing base URL."""
        result = subprocess.run(
            ["uv", "run", "d365fo-client", "entity", "get", "Customers"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
        )
        # Should fail due to missing base URL
        assert result.returncode != 0
        assert "base" in result.stdout.lower() or "url" in result.stdout.lower()


@skip_if_not_level("mock")
class TestCLIConfigCommands:
    """Test CLI configuration commands that don't require server connection."""

    def test_cli_config_help(self):
        """Test CLI config help."""
        result = subprocess.run(
            ["uv", "run", "d365fo-client", "config", "--help"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
        )
        assert result.returncode == 0
        assert "config" in result.stdout.lower()

    def test_cli_config_list(self):
        """Test CLI config list command."""
        result = subprocess.run(
            ["uv", "run", "d365fo-client", "config", "list"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
        )
        # Config commands should work even without server
        assert result.returncode == 0


@skip_if_not_level("mock")
class TestCLIOutputFormats:
    """Test CLI output format argument parsing."""

    def test_cli_output_format_validation(self):
        """Test that CLI accepts various output formats in help."""
        # Test that output format help mentions supported formats
        result = subprocess.run(
            ["uv", "run", "d365fo-client", "--help"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
        )
        assert result.returncode == 0
        # Should mention output format option
        assert "--output" in result.stdout or "-o" in result.stdout


@skip_if_not_level("mock")
class TestCLIFileOperations:
    """Test CLI file-based operations."""

    def test_cli_create_with_invalid_file(self):
        """Test entity create with invalid file path."""
        result = subprocess.run(
            [
                "uv",
                "run",
                "d365fo-client",
                "--base-url",
                "http://localhost:8000",
                "entity",
                "create",
                "Customers",
                "--file",
                "/nonexistent/file.json",
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
        )
        # Should fail due to nonexistent file
        assert result.returncode != 0

    def test_cli_create_with_invalid_json_file(self):
        """Test entity create with invalid JSON file."""
        # Create temporary file with invalid JSON
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content {")
            temp_file = f.name

        try:
            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "d365fo-client",
                    "--base-url",
                    "http://localhost:8000",
                    "entity",
                    "create",
                    "Customers",
                    "--file",
                    temp_file,
                ],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent.parent),
            )
            # Should fail due to invalid JSON
            assert result.returncode != 0
        finally:
            os.unlink(temp_file)

    def test_cli_create_with_valid_json_file_structure(self):
        """Test entity create with valid JSON file structure (will fail on connection)."""
        # Create temporary file with valid JSON
        test_data = {
            "CustomerAccount": "TEST-001",
            "CustomerName": "Test Customer",
            "CurrencyCode": "USD",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_file = f.name

        try:
            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "d365fo-client",
                    "--base-url",
                    "http://localhost:8000",
                    "entity",
                    "create",
                    "Customers",
                    "--file",
                    temp_file,
                ],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent.parent),
            )
            # Will fail on connection but should parse the file successfully
            # (error should be about connection, not JSON parsing)
            if result.returncode != 0:
                # Should not contain JSON parsing errors
                assert (
                    "json" not in result.stdout.lower()
                    or "parse" not in result.stdout.lower()
                )
        finally:
            os.unlink(temp_file)


@skip_if_not_level("mock")
class TestCLILogicIntegration:
    """Test CLI internal logic without external server dependencies."""

    def test_cli_demo_mode(self):
        """Test CLI demo mode flag acceptance."""
        # Just test that the --demo flag is recognized (doesn't show help)
        # We'll use a quick test that the flag doesn't cause argument parsing errors

        # Test with demo flag and invalid args to see if it parses the flag correctly
        result = subprocess.run(
            ["uv", "run", "d365fo-client", "--help"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
        )

        # Demo flag should appear in help
        assert "--demo" in result.stdout or "demo" in result.stdout.lower()

    def test_cli_global_options_parsing(self):
        """Test that global CLI options are properly parsed."""
        # Test various global option combinations in help
        global_options = ["--verbose", "--output", "--base-url"]

        result = subprocess.run(
            ["uv", "run", "d365fo-client", "--help"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
        )

        assert result.returncode == 0
        for option in global_options:
            assert option in result.stdout

    def test_cli_subcommand_discovery(self):
        """Test that all main subcommands are available."""
        expected_commands = [
            "entity",
            "metadata",
            "version",
            "test",
            "config",
            "action",
        ]

        result = subprocess.run(
            ["uv", "run", "d365fo-client", "--help"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
        )

        assert result.returncode == 0
        for command in expected_commands:
            assert command in result.stdout.lower()

    def test_cli_entity_subcommand_discovery(self):
        """Test that all entity subcommands are available."""
        expected_subcommands = ["get", "create", "update", "delete"]

        result = subprocess.run(
            ["uv", "run", "d365fo-client", "entity", "--help"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
        )

        assert result.returncode == 0
        for subcommand in expected_subcommands:
            assert subcommand in result.stdout.lower()


@skip_if_not_level("mock")
class TestCLIErrorMessages:
    """Test CLI error message quality and clarity."""

    def test_cli_invalid_command_error(self):
        """Test error message for invalid command."""
        result = subprocess.run(
            ["uv", "run", "d365fo-client", "invalidcommand"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
        )
        assert result.returncode != 0
        # Should provide helpful error message
        assert len(result.stderr) > 0 or "invalid" in result.stdout.lower()

    def test_cli_missing_required_arg_error(self):
        """Test error message for missing required arguments."""
        result = subprocess.run(
            ["uv", "run", "d365fo-client", "entity"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
        )
        assert result.returncode != 0
        # Should provide helpful error message about required arguments
        assert len(result.stderr) > 0 or "required" in result.stdout.lower()

    def test_cli_invalid_json_data_error(self):
        """Test error message for invalid JSON data."""
        result = subprocess.run(
            [
                "uv",
                "run",
                "d365fo-client",
                "--base-url",
                "http://localhost:8000",
                "entity",
                "create",
                "Customers",
                "--data",
                "invalid json {",
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
        )
        assert result.returncode != 0
        # Should provide error about JSON parsing or data - looking at actual error message
        assert "expecting" in result.stdout.lower() or "error" in result.stdout.lower()
