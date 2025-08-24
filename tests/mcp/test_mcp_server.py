"""Tests for MCP server functionality."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from d365fo_client.mcp import D365FOMCPServer


class TestD365FOMCPServer:
    """Test MCP server."""

    def test_init(self):
        """Test MCP server initialization."""
        config = {"default_environment": {"base_url": "https://test.dynamics.com"}}
        server = D365FOMCPServer(config)

        assert server.config == config
        assert server.client_manager is not None
        assert server.entity_handler is not None
        assert server.environment_handler is not None
        assert server.connection_tools is not None

    def test_load_default_config(self):
        """Test loading default configuration."""
        server = D365FOMCPServer()

        config = server._load_default_config()

        assert "default_environment" in config
        assert "cache" in config
        assert "performance" in config
        assert "security" in config
        assert "profiles" in config

        # Test environment variable handling
        with patch.dict("os.environ", {"D365FO_BASE_URL": "https://env.dynamics.com"}):
            config = server._load_default_config()
            assert (
                config["default_environment"]["base_url"] == "https://env.dynamics.com"
            )


# Integration test to verify basic functionality
@pytest.mark.asyncio
async def test_mcp_server_basic_functionality():
    """Test basic MCP server functionality."""
    # Mock environment to avoid actual D365FO connections
    with patch.dict("os.environ", {"D365FO_BASE_URL": "https://mock.dynamics.com"}):
        server = D365FOMCPServer()

        # Test that we can create the server without errors
        assert server is not None
        assert server.client_manager is not None

        # Test cleanup (should not raise errors)
        await server.cleanup()
