"""Tests for MCP tools functionality."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from d365fo_client.mcp.tools import (
    ConnectionTools,
    CrudTools,
    LabelTools,
    MetadataTools,
)


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
        response = json.loads(result[0].text)
        assert "success" in response
        assert "endpoints" in response
        assert "responseTime" in response


class TestCrudTools:
    """Test CRUD tools."""

    def test_get_tools(self):
        """Test getting CRUD tool definitions."""
        client_manager = MagicMock()
        tools = CrudTools(client_manager)

        tool_list = tools.get_tools()
        assert len(tool_list) == 6  # Updated to match current implementation

        tool_names = [tool.name for tool in tool_list]
        expected_tools = [
            "d365fo_query_entities",
            "d365fo_get_entity_record",
            "d365fo_create_entity_record",
            "d365fo_update_entity_record",
            "d365fo_delete_entity_record",
            "d365fo_call_action",  # This was the 6th tool causing the test failure
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
            "d365fo_get_enumeration_fields",
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
        expected_tools = ["d365fo_get_label", "d365fo_get_labels_batch"]

        for expected_tool in expected_tools:
            assert expected_tool in tool_names
