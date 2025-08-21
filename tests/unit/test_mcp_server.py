"""Tests for MCP server functionality."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from d365fo_client.mcp import D365FOMCPServer, D365FOClientManager
from d365fo_client.mcp.tools import ConnectionTools, CrudTools, MetadataTools, LabelTools
from d365fo_client.mcp.resources import EntityResourceHandler, EnvironmentResourceHandler


class TestD365FOClientManager:
    """Test D365FO client manager."""
    
    def test_init(self):
        """Test client manager initialization."""
        config = {"default_environment": {"base_url": "https://test.dynamics.com"}}
        manager = D365FOClientManager(config)
        
        assert manager.config == config
        assert manager._client_pool == {}
        assert manager._session_lock is not None
    
    @pytest.mark.asyncio
    async def test_build_client_config(self):
        """Test building client config from profile."""
        config = {
            "default_environment": {
                "base_url": "https://default.dynamics.com",
                "use_default_credentials": True
            },
            "profiles": {
                "test": {
                    "base_url": "https://test.dynamics.com",
                    "timeout": 120
                }
            }
        }
        
        manager = D365FOClientManager(config)
        
        # Test default profile
        default_config = manager._build_client_config("default")
        assert default_config.base_url == "https://usnconeboxax1aos.cloud.onebox.dynamics.com"
        assert default_config.use_default_credentials is True
        
        # Test specific profile
        test_config = manager._build_client_config("test")
        assert test_config.base_url == "https://test.dynamics.com"
        assert test_config.timeout == 120
        assert test_config.use_default_credentials is True  # Inherited from default


class TestConnectionTools:
    """Test connection tools."""
    
    def test_init(self):
        """Test connection tools initialization."""
        client_manager = MagicMock()
        tools = ConnectionTools(client_manager)
        
        assert tools.client_manager == client_manager
    
    def test_get_tools(self):
        """Test getting tool definitions."""
        client_manager = MagicMock()
        tools = ConnectionTools(client_manager)
        
        tool_list = tools.get_tools()
        assert len(tool_list) == 2
        
        tool_names = [tool.name for tool in tool_list]
        assert "d365fo_test_connection" in tool_names
        assert "d365fo_get_environment_info" in tool_names
    
    @pytest.mark.asyncio
    async def test_execute_test_connection(self):
        """Test executing test connection tool."""
        client_manager = AsyncMock()
        client_manager.test_connection.return_value = True
        
        tools = ConnectionTools(client_manager)
        
        result = await tools.execute_test_connection({})
        
        assert len(result) == 1
        assert result[0].type == "text"
        
        # Verify the response contains expected fields
        import json
        response = json.loads(result[0].text)
        assert "success" in response
        assert "endpoints" in response
        assert "responseTime" in response


class TestEntityResourceHandler:
    """Test entity resource handler."""
    
    def test_init(self):
        """Test entity resource handler initialization."""
        client_manager = MagicMock()
        handler = EntityResourceHandler(client_manager)
        
        assert handler.client_manager == client_manager
    
    @pytest.mark.asyncio
    async def test_list_resources(self):
        """Test listing entity resources."""
        client_manager = AsyncMock()
        mock_client = MagicMock()  # Use regular mock for synchronous search_entities
        mock_client.search_entities.return_value = ["Customers", "Vendors", "Products"]
        client_manager.get_client.return_value = mock_client
        
        handler = EntityResourceHandler(client_manager)
        
        resources = await handler.list_resources()
        
        assert len(resources) == 3
        assert all(str(r.uri).startswith("d365fo://entities/") for r in resources)
        assert any("Customers" in str(r.uri) for r in resources)
    
    def test_extract_entity_name(self):
        """Test extracting entity name from URI."""
        client_manager = MagicMock()
        handler = EntityResourceHandler(client_manager)
        
        entity_name = handler._extract_entity_name("d365fo://entities/Customers")
        assert entity_name == "Customers"
        
        # Test invalid URI
        with pytest.raises(ValueError):
            handler._extract_entity_name("invalid://uri")


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
        with patch.dict('os.environ', {'D365FO_BASE_URL': 'https://env.dynamics.com'}):
            config = server._load_default_config()
            assert config["default_environment"]["base_url"] == "https://env.dynamics.com"


class TestCrudTools:
    """Test CRUD tools."""
    
    def test_get_tools(self):
        """Test getting CRUD tool definitions."""
        client_manager = MagicMock()
        tools = CrudTools(client_manager)
        
        tool_list = tools.get_tools()
        assert len(tool_list) == 5
        
        tool_names = [tool.name for tool in tool_list]
        expected_tools = [
            "d365fo_query_entities",
            "d365fo_get_entity_record", 
            "d365fo_create_entity_record",
            "d365fo_update_entity_record",
            "d365fo_delete_entity_record"
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names


class TestMetadataTools:
    """Test metadata tools."""
    
    def test_get_tools(self):
        """Test getting metadata tool definitions."""
        client_manager = MagicMock()
        tools = MetadataTools(client_manager)
        
        tool_list = tools.get_tools()
        assert len(tool_list) == 5
        
        tool_names = [tool.name for tool in tool_list]
        expected_tools = [
            "d365fo_search_entities",
            "d365fo_get_entity_schema",
            "d365fo_search_actions",
            "d365fo_search_enumerations",
            "d365fo_get_enumeration_fields"
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names


class TestLabelTools:
    """Test label tools."""
    
    def test_get_tools(self):
        """Test getting label tool definitions."""
        client_manager = MagicMock()
        tools = LabelTools(client_manager)
        
        tool_list = tools.get_tools()
        assert len(tool_list) == 2
        
        tool_names = [tool.name for tool in tool_list]
        expected_tools = [
            "d365fo_get_label",
            "d365fo_get_labels_batch"
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names


# Integration test to verify basic functionality
@pytest.mark.asyncio
async def test_mcp_server_basic_functionality():
    """Test basic MCP server functionality."""
    # Mock environment to avoid actual D365FO connections
    with patch.dict('os.environ', {'D365FO_BASE_URL': 'https://mock.dynamics.com'}):
        server = D365FOMCPServer()
        
        # Test that we can create the server without errors
        assert server is not None
        assert server.client_manager is not None
        
        # Test cleanup (should not raise errors)
        await server.cleanup()