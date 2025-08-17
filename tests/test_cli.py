"""Tests for CLI functionality."""

import pytest
import argparse
import json
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch, mock_open
from io import StringIO
import sys

from d365fo_client.cli import CLIManager
from d365fo_client.config import ConfigManager, CLIProfile
from d365fo_client.output import OutputFormatter, format_success_message, format_error_message
from d365fo_client.main import create_argument_parser
from d365fo_client.models import FOClientConfig


class TestOutputFormatter:
    """Test output formatting functionality."""
    
    def test_json_output(self):
        """Test JSON output formatting."""
        formatter = OutputFormatter("json")
        data = {"name": "test", "value": 123}
        result = formatter.format_output(data)
        
        assert json.loads(result) == data
    
    def test_table_output_dict(self):
        """Test table output formatting for dictionary."""
        formatter = OutputFormatter("table")
        data = {"name": "test", "value": 123}
        result = formatter.format_output(data)
        
        assert "Property" in result
        assert "Value" in result
        assert "test" in result
        assert "123" in result
    
    def test_table_output_list(self):
        """Test table output formatting for list of dictionaries."""
        formatter = OutputFormatter("table")
        data = [
            {"name": "test1", "value": 123},
            {"name": "test2", "value": 456}
        ]
        result = formatter.format_output(data)
        
        assert "name" in result
        assert "value" in result
        assert "test1" in result
        assert "test2" in result
    
    def test_csv_output(self):
        """Test CSV output formatting."""
        formatter = OutputFormatter("csv")
        data = [
            {"name": "test1", "value": 123},
            {"name": "test2", "value": 456}
        ]
        result = formatter.format_output(data)
        
        lines = result.strip().split('\n')
        assert len(lines) == 3  # header + 2 data rows
        assert "name,value" in lines[0]
    
    def test_yaml_output(self):
        """Test YAML output formatting."""
        formatter = OutputFormatter("yaml")
        data = {"name": "test", "value": 123}
        result = formatter.format_output(data)
        
        assert "name: test" in result
        assert "value: 123" in result
    
    def test_unsupported_format(self):
        """Test unsupported format raises error."""
        with pytest.raises(ValueError):
            OutputFormatter("unsupported")


class TestConfigManager:
    """Test configuration management functionality."""
    
    def setup_method(self):
        """Setup test configuration manager with temporary config file."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml')
        self.temp_file.close()
        self.config_manager = ConfigManager(self.temp_file.name)
    
    def teardown_method(self):
        """Clean up temporary files."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_empty_config(self):
        """Test loading empty configuration."""
        profiles = self.config_manager.list_profiles()
        assert len(profiles) == 0
        
        default_profile = self.config_manager.get_default_profile()
        assert default_profile is None
    
    def test_save_and_load_profile(self):
        """Test saving and loading profiles."""
        profile = CLIProfile(
            name="test",
            base_url="https://test.dynamics.com",
            auth_mode="default"
        )
        
        self.config_manager.save_profile(profile)
        
        loaded_profile = self.config_manager.get_profile("test")
        assert loaded_profile is not None
        assert loaded_profile.name == "test"
        assert loaded_profile.base_url == "https://test.dynamics.com"
    
    def test_delete_profile(self):
        """Test deleting profiles."""
        profile = CLIProfile(
            name="test",
            base_url="https://test.dynamics.com"
        )
        
        self.config_manager.save_profile(profile)
        assert self.config_manager.get_profile("test") is not None
        
        success = self.config_manager.delete_profile("test")
        assert success is True
        assert self.config_manager.get_profile("test") is None
        
        # Try to delete non-existent profile
        success = self.config_manager.delete_profile("nonexistent")
        assert success is False
    
    def test_default_profile(self):
        """Test setting and getting default profile."""
        profile = CLIProfile(
            name="test",
            base_url="https://test.dynamics.com"
        )
        
        self.config_manager.save_profile(profile)
        
        success = self.config_manager.set_default_profile("test")
        assert success is True
        
        default_profile = self.config_manager.get_default_profile()
        assert default_profile is not None
        assert default_profile.name == "test"
        
        # Try to set non-existent profile as default
        success = self.config_manager.set_default_profile("nonexistent")
        assert success is False
    
    def test_effective_config_from_args(self):
        """Test building effective config from arguments."""
        args = argparse.Namespace(
            base_url="https://test.dynamics.com",
            client_id=None,
            client_secret=None,
            tenant_id=None,
            verify_ssl=True,
            label_cache=True,
            label_expiry=60,
            profile=None
        )
        
        config = self.config_manager.get_effective_config(args)
        
        assert isinstance(config, FOClientConfig)
        assert config.base_url == "https://test.dynamics.com"
        assert config.use_default_credentials is True
        assert config.verify_ssl is True


class TestCLIManager:
    """Test CLI manager functionality."""
    
    @pytest.mark.asyncio
    async def test_demo_mode(self):
        """Test demo mode execution."""
        cli_manager = CLIManager()
        
        args = argparse.Namespace(demo=True, output="json")
        
        # Mock the example_usage function
        with patch('d365fo_client.main.example_usage', new_callable=AsyncMock) as mock_example:
            result = await cli_manager.execute_command(args)
            
            assert result == 0
            mock_example.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_config_list_empty(self):
        """Test config list command with no profiles."""
        cli_manager = CLIManager()
        
        args = argparse.Namespace(
            demo=False,
            command="config",
            config_subcommand="list",
            output="json"
        )
        
        # Capture stdout
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            result = await cli_manager.execute_command(args)
        
        assert result == 0
        assert "No configuration profiles found" in captured_output.getvalue()
    
    @pytest.mark.asyncio
    async def test_missing_base_url(self):
        """Test error when base URL is missing."""
        cli_manager = CLIManager()
        
        args = argparse.Namespace(
            demo=False,
            command="test",
            output="json",
            base_url=None,
            profile=None
        )
        
        # Capture stdout
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            result = await cli_manager.execute_command(args)
        
        assert result == 1
        assert "Base URL is required" in captured_output.getvalue()
    
    @pytest.mark.asyncio
    async def test_test_command_success(self):
        """Test successful test command execution."""
        cli_manager = CLIManager()
        
        args = argparse.Namespace(
            demo=False,
            command="test",
            output="json",
            base_url="https://test.dynamics.com",
            profile=None,
            odata_only=False,
            metadata_only=False,
            verbose=False
        )
        
        # Mock FOClient
        with patch('d365fo_client.cli.FOClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.test_connection.return_value = True
            mock_client.test_metadata_connection.return_value = True
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Capture stdout
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                result = await cli_manager.execute_command(args)
            
            assert result == 0
            output = captured_output.getvalue()
            assert "✅" in output
            assert "successful" in output
    
    @pytest.mark.asyncio
    async def test_version_command(self):
        """Test version command execution."""
        cli_manager = CLIManager()
        
        args = argparse.Namespace(
            demo=False,
            command="version",
            output="json",
            base_url="https://test.dynamics.com",
            profile=None,
            application=True,
            platform=False,
            build=False,
            all=False,
            verbose=False
        )
        
        # Mock FOClient
        with patch('d365fo_client.cli.FOClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_application_version.return_value = "10.0.12345"
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Capture stdout
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                result = await cli_manager.execute_command(args)
            
            assert result == 0
            output = captured_output.getvalue()
            # Should contain JSON with application version
            assert "10.0.12345" in output


class TestArgumentParser:
    """Test argument parser functionality."""
    
    def test_basic_parser_creation(self):
        """Test basic parser creation and structure."""
        parser = create_argument_parser()
        
        assert parser is not None
        assert parser.prog == "d365fo-client"
    
    def test_demo_argument(self):
        """Test demo argument parsing."""
        parser = create_argument_parser()
        
        args = parser.parse_args(["--demo"])
        assert args.demo is True
    
    def test_version_command(self):
        """Test version command parsing."""
        parser = create_argument_parser()
        
        args = parser.parse_args(["--base-url", "https://test.com", "version", "--application"])
        assert args.command == "version"
        assert args.application is True
        assert args.base_url == "https://test.com"
    
    def test_test_command(self):
        """Test test command parsing."""
        parser = create_argument_parser()
        
        args = parser.parse_args(["--base-url", "https://test.com", "test", "--odata-only"])
        assert args.command == "test"
        assert args.odata_only is True
        assert args.base_url == "https://test.com"
    
    def test_metadata_search_command(self):
        """Test metadata search command parsing."""
        parser = create_argument_parser()
        
        args = parser.parse_args([
            "--base-url", "https://test.com", 
            "metadata", "search", "customer", 
            "--type", "entities", 
            "--limit", "10"
        ])
        assert args.command == "metadata"
        assert args.metadata_subcommand == "search"
        assert args.pattern == "customer"
        assert args.type == "entities"
        assert args.limit == 10
    
    def test_entity_get_command(self):
        """Test entity get command parsing."""
        parser = create_argument_parser()
        
        args = parser.parse_args([
            "--base-url", "https://test.com",
            "entity", "get", "Customers", "US-001",
            "--select", "CustomerAccount,Name",
            "--top", "5"
        ])
        assert args.command == "entity"
        assert args.entity_subcommand == "get"
        assert args.entity_name == "Customers"
        assert args.key == "US-001"
        assert args.select == "CustomerAccount,Name"
        assert args.top == 5
    
    def test_config_create_command(self):
        """Test config create command parsing."""
        parser = create_argument_parser()
        
        args = parser.parse_args([
            "config", "create", "test-profile",
            "--base-url", "https://test.com",
            "--auth-mode", "explicit"
        ])
        assert args.command == "config"
        assert args.config_subcommand == "create"
        assert args.profile_name == "test-profile"
        assert args.base_url == "https://test.com"
        assert args.auth_mode == "explicit"


class TestMessageFormatters:
    """Test message formatting functions."""
    
    def test_success_message(self):
        """Test success message formatting."""
        message = format_success_message("Test successful")
        assert "✅" in message
        assert "Test successful" in message
    
    def test_error_message(self):
        """Test error message formatting."""
        message = format_error_message("Test failed")
        assert "❌" in message
        assert "Test failed" in message


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple components."""
    
    @pytest.mark.asyncio
    async def test_config_workflow(self):
        """Test complete configuration workflow."""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as temp_file:
            config_path = temp_file.name
        
        try:
            cli_manager = CLIManager()
            cli_manager.config_manager = ConfigManager(config_path)
            
            # Test creating a profile
            create_args = argparse.Namespace(
                demo=False,
                command="config",
                config_subcommand="create",
                profile_name="test-profile",
                base_url="https://test.dynamics.com",
                auth_mode="default",
                client_id=None,
                client_secret=None,
                tenant_id=None,
                verify_ssl=True,
                output_format="table",
                label_cache=True,
                label_expiry=60,
                language="en-US",
                output="json"
            )
            
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                result = await cli_manager.execute_command(create_args)
            
            assert result == 0
            assert "created successfully" in captured_output.getvalue()
            
            # Test listing profiles
            list_args = argparse.Namespace(
                demo=False,
                command="config",
                config_subcommand="list",
                output="json"
            )
            
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                result = await cli_manager.execute_command(list_args)
            
            assert result == 0
            output = captured_output.getvalue()
            assert "test-profile" in output
            
        finally:
            # Clean up
            if os.path.exists(config_path):
                os.unlink(config_path)