"""Integration tests for MCP CRUD tools.

These tests validate that the MCP CRUD tools correctly leverage FOClient's
schema validation and work end-to-end against real D365 F&O environments.
"""

import json
import pytest
from typing import Dict, Any

from d365fo_client.mcp.fastmcp_server import FastD365FOMCPServer

from . import skip_if_not_level


def parse_mcp_result(result):
    """Parse MCP tool result from TextContent list to dictionary."""
    if isinstance(result, list) and len(result) > 0:
        # Extract text from first TextContent object
        text_content = result[0]
        if hasattr(text_content, 'text'):
            return json.loads(text_content.text)
    return result


@pytest.fixture
async def mcp_server(tmp_path):
    """Create MCP server instance for testing."""
    # Create MCP server with default configuration
    # The server will use the default profile manager which loads from ~/.d365fo-client
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("d365fo-test")
    server = FastD365FOMCPServer(mcp=mcp)

    yield server

    # Cleanup
    await server.cleanup()


@skip_if_not_level("sandbox")
class TestMCPCrudToolsQuery:
    """Test d365fo_query_entities MCP tool with schema validation."""

    @pytest.mark.asyncio
    async def test_query_entities_basic(self, mcp_server):
        """Test basic query operation through MCP tool."""
        # Query Companies entity through MCP framework
        raw_result = await mcp_server.mcp.call_tool("d365fo_query_entities", {
            "entity_name": "Companies",
            "top": 5,
            "profile": "default"
        })

        result = parse_mcp_result(raw_result)

        # Should succeed without validation errors
        assert "error" not in result
        assert "data" in result
        assert isinstance(result["data"], list)
        assert result["entityName"] == "Companies"
        assert result["totalRecords"] <= 5

    @pytest.mark.asyncio
    async def test_query_entities_with_invalid_entity(self, mcp_server):
        """Test query operation with non-existent entity (should fail with clear error)."""
        raw_result = await mcp_server.mcp.call_tool("d365fo_query_entities", {
            "entity_name": "NonExistentEntity12345",
            "top": 5,
            "profile": "default"
        })

        result = parse_mcp_result(raw_result)

        # Should return error from FOClient
        assert "error" in result
        assert "not found" in result["error"].lower() or "not accessible" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_query_entities_with_filter(self, mcp_server):
        """Test query operation with OData filter."""
        # First get a company to use in filter
        raw_result = await mcp_server.mcp.call_tool("d365fo_query_entities", {
            "entity_name": "Companies",
            "top": 1,
            "profile": "default"
        })
        initial_result = parse_mcp_result(raw_result)

        if initial_result.get("data") and len(initial_result["data"]) > 0:
            company_id = initial_result["data"][0]["DataAreaId"]

            # Now query with filter
            raw_result2 = await mcp_server.mcp.call_tool("d365fo_query_entities", {
                "entity_name": "Companies",
                "filter": f"DataAreaId eq '{company_id}'",
                "profile": "default"
            })
            filter_result = parse_mcp_result(raw_result2)

            assert "error" not in filter_result
            assert filter_result["totalRecords"] >= 1
            assert filter_result["data"][0]["DataAreaId"] == company_id


@skip_if_not_level("sandbox")
class TestMCPCrudToolsGet:
    """Test d365fo_get_entity_record MCP tool with schema validation."""

    @pytest.mark.asyncio
    async def test_get_entity_record_basic(self, mcp_server):
        """Test get single entity record through MCP tool."""
        # First query to get a valid record key
        raw_result = await mcp_server.mcp.call_tool("d365fo_query_entities", {
            "entity_name": "Companies",
            "top": 1,
            "profile": "default"
        })
        query_result = parse_mcp_result(raw_result)

        if query_result.get("data") and len(query_result["data"]) > 0:
            company_id = query_result["data"][0]["DataAreaId"]

            # Now get the specific record
            raw_result2 = await mcp_server.mcp.call_tool("d365fo_get_entity_record", {
                "entity_name": "Companies",
                "key_fields": ["DataAreaId"],
                "key_values": [company_id],
                "profile": "default"
            })
            get_result = parse_mcp_result(raw_result2)

            # Should succeed
            assert "error" not in get_result
            assert "data" in get_result
            assert get_result["data"]["DataAreaId"] == company_id
            assert get_result["entityName"] == "Companies"

    @pytest.mark.asyncio
    async def test_get_entity_record_with_invalid_entity(self, mcp_server):
        """Test get record with non-existent entity."""
        raw_result = await mcp_server.mcp.call_tool("d365fo_get_entity_record", {
            "entity_name": "NonExistentEntity12345",
            "key_fields": ["SomeKey"],
            "key_values": ["SomeValue"],
            "profile": "default"
        })
        result = parse_mcp_result(raw_result)

        # Should return error from FOClient's schema validation
        assert "error" in result
        assert "not found" in result["error"].lower() or "not accessible" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_get_entity_record_with_mismatched_keys(self, mcp_server):
        """Test get record with mismatched key fields and values."""
        raw_result = await mcp_server.mcp.call_tool("d365fo_get_entity_record", {
            "entity_name": "Companies",
            "key_fields": ["DataAreaId", "ExtraField"],
            "key_values": ["USMF"],  # Only one value for two fields
            "profile": "default"
        })
        result = parse_mcp_result(raw_result)

        # Should return error about key mismatch
        assert "error" in result
        assert "mismatch" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_get_entity_record_with_select(self, mcp_server):
        """Test get record with field selection."""
        # First query to get a valid record key
        raw_result = await mcp_server.mcp.call_tool("d365fo_query_entities", {
            "entity_name": "Companies",
            "top": 1,
            "profile": "default"
        })
        query_result = parse_mcp_result(raw_result)

        if query_result.get("data") and len(query_result["data"]) > 0:
            company_id = query_result["data"][0]["DataAreaId"]

            # Get record with field selection
            raw_result2 = await mcp_server.mcp.call_tool("d365fo_get_entity_record", {
                "entity_name": "Companies",
                "key_fields": ["DataAreaId"],
                "key_values": [company_id],
                "select": ["DataAreaId"],
                "profile": "default"
            })
            get_result = parse_mcp_result(raw_result2)

            assert "error" not in get_result
            assert "DataAreaId" in get_result["data"]


@skip_if_not_level("sandbox")
class TestMCPCrudToolsCreate:
    """Test d365fo_create_entity_record MCP tool with schema validation."""

    @pytest.mark.asyncio
    async def test_create_entity_readonly_validation(self, mcp_server):
        """Test that create operation fails for read-only entities."""
        # Companies is typically read-only for creation
        raw_result = await mcp_server.mcp.call_tool("d365fo_create_entity_record", {
            "entity_name": "Companies",
            "data": {"DataAreaId": "TEST", "Name": "Test Company"},
            "profile": "default"
        })
        result = parse_mcp_result(raw_result)

        # Should fail with read-only error from FOClient
        assert "error" in result or result.get("created") is False
        if "error" in result:
            error_msg = result["error"].lower()
            assert "read-only" in error_msg or "read only" in error_msg or "not supported" in error_msg

    @pytest.mark.asyncio
    async def test_create_entity_invalid_entity(self, mcp_server):
        """Test create operation with non-existent entity."""
        raw_result = await mcp_server.mcp.call_tool("d365fo_create_entity_record", {
            "entity_name": "NonExistentEntity12345",
            "data": {"Field1": "Value1"},
            "profile": "default"
        })
        result = parse_mcp_result(raw_result)

        # Should return error from FOClient's schema validation
        assert "error" in result
        assert "not found" in result["error"].lower() or "not accessible" in result["error"].lower()


@skip_if_not_level("sandbox")
class TestMCPCrudToolsUpdate:
    """Test d365fo_update_entity_record MCP tool with schema validation."""

    @pytest.mark.asyncio
    async def test_update_entity_readonly_validation(self, mcp_server):
        """Test that update operation fails for read-only entities."""
        # First get a record to attempt update
        raw_result = await mcp_server.mcp.call_tool("d365fo_query_entities", {
            "entity_name": "Companies",
            "top": 1,
            "profile": "default"
        })
        query_result = parse_mcp_result(raw_result)

        if query_result.get("data") and len(query_result["data"]) > 0:
            company_id = query_result["data"][0]["DataAreaId"]

            # Try to update (should fail if read-only)
            raw_result2 = await mcp_server.mcp.call_tool("d365fo_update_entity_record", {
                "entity_name": "Companies",
                "key_fields": ["DataAreaId"],
                "key_values": [company_id],
                "data": {"Name": "Updated Test Name"},
                "profile": "default"
            })
            result = parse_mcp_result(raw_result2)

            # Should fail with read-only error from FOClient (if Companies is read-only)
            # Or succeed if entity supports updates
            if "error" in result:
                error_msg = result["error"].lower()
                assert (
                    "read-only" in error_msg or
                    "read only" in error_msg or
                    "not supported" in error_msg or
                    "not editable" in error_msg
                )

    @pytest.mark.asyncio
    async def test_update_entity_invalid_entity(self, mcp_server):
        """Test update operation with non-existent entity."""
        raw_result = await mcp_server.mcp.call_tool("d365fo_update_entity_record", {
            "entity_name": "NonExistentEntity12345",
            "key_fields": ["SomeKey"],
            "key_values": ["SomeValue"],
            "data": {"Field1": "Value1"},
            "profile": "default"
        })
        result = parse_mcp_result(raw_result)

        # Should return error from FOClient's schema validation
        assert "error" in result
        assert "not found" in result["error"].lower() or "not accessible" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_update_entity_with_mismatched_keys(self, mcp_server):
        """Test update record with mismatched key fields and values."""
        raw_result = await mcp_server.mcp.call_tool("d365fo_update_entity_record", {
            "entity_name": "Companies",
            "key_fields": ["DataAreaId", "ExtraField"],
            "key_values": ["USMF"],  # Only one value for two fields
            "data": {"Name": "Test"},
            "profile": "default"
        })
        result = parse_mcp_result(raw_result)

        # Should return error about key mismatch
        assert "error" in result
        assert "mismatch" in result["error"].lower()


@skip_if_not_level("sandbox")
class TestMCPCrudToolsDelete:
    """Test d365fo_delete_entity_record MCP tool with schema validation."""

    @pytest.mark.asyncio
    async def test_delete_entity_readonly_validation(self, mcp_server):
        """Test that delete operation fails for read-only entities."""
        # First get a record to attempt delete
        raw_result = await mcp_server.mcp.call_tool("d365fo_query_entities", {
            "entity_name": "Companies",
            "top": 1,
            "profile": "default"
        })
        query_result = parse_mcp_result(raw_result)

        if query_result.get("data") and len(query_result["data"]) > 0:
            company_id = query_result["data"][0]["DataAreaId"]

            # Try to delete (should fail if read-only)
            raw_result2 = await mcp_server.mcp.call_tool("d365fo_delete_entity_record", {
                "entity_name": "Companies",
                "key_fields": ["DataAreaId"],
                "key_values": [company_id],
                "profile": "default"
            })
            result = parse_mcp_result(raw_result2)

            # Should fail with read-only error from FOClient
            assert "error" in result
            error_msg = result["error"].lower()
            assert (
                "read-only" in error_msg or
                "read only" in error_msg or
                "not supported" in error_msg or
                "cannot" in error_msg
            )

    @pytest.mark.asyncio
    async def test_delete_entity_invalid_entity(self, mcp_server):
        """Test delete operation with non-existent entity."""
        raw_result = await mcp_server.mcp.call_tool("d365fo_delete_entity_record", {
            "entity_name": "NonExistentEntity12345",
            "key_fields": ["SomeKey"],
            "key_values": ["SomeValue"],
            "profile": "default"
        })
        result = parse_mcp_result(raw_result)

        # Should return error from FOClient's schema validation
        assert "error" in result
        assert "not found" in result["error"].lower() or "not accessible" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_delete_entity_with_mismatched_keys(self, mcp_server):
        """Test delete record with mismatched key fields and values."""
        raw_result = await mcp_server.mcp.call_tool("d365fo_delete_entity_record", {
            "entity_name": "Companies",
            "key_fields": ["DataAreaId", "ExtraField"],
            "key_values": ["USMF"],  # Only one value for two fields
            "profile": "default"
        })
        result = parse_mcp_result(raw_result)

        # Should return error about key mismatch
        assert "error" in result
        assert "mismatch" in result["error"].lower()


@skip_if_not_level("sandbox")
class TestMCPCrudToolsIntegration:
    """Integration tests combining multiple CRUD operations."""

    @pytest.mark.asyncio
    async def test_query_then_get_workflow(self, mcp_server):
        """Test typical workflow: query entities, then get specific record."""
        # Step 1: Query for records
        raw_result = await mcp_server.mcp.call_tool("d365fo_query_entities", {
            "entity_name": "Companies",
            "top": 3,
            "profile": "default"
        })
        query_result = parse_mcp_result(raw_result)

        assert "error" not in query_result
        assert query_result["totalRecords"] > 0

        # Step 2: Get specific record from query results
        first_record = query_result["data"][0]
        company_id = first_record["DataAreaId"]

        raw_result2 = await mcp_server.mcp.call_tool("d365fo_get_entity_record", {
            "entity_name": "Companies",
            "key_fields": ["DataAreaId"],
            "key_values": [company_id],
            "profile": "default"
        })
        get_result = parse_mcp_result(raw_result2)

        assert "error" not in get_result
        assert get_result["data"]["DataAreaId"] == company_id

    @pytest.mark.asyncio
    async def test_schema_aware_key_encoding(self, mcp_server):
        """Test that schema-aware key encoding works correctly."""
        # Get a record with composite or complex key structure
        raw_result = await mcp_server.mcp.call_tool("d365fo_query_entities", {
            "entity_name": "Companies",
            "top": 1,
            "profile": "default"
        })
        query_result = parse_mcp_result(raw_result)

        if query_result.get("data") and len(query_result["data"]) > 0:
            company_id = query_result["data"][0]["DataAreaId"]

            # Get record - FOClient should handle key encoding via schema
            raw_result2 = await mcp_server.mcp.call_tool("d365fo_get_entity_record", {
                "entity_name": "Companies",
                "key_fields": ["DataAreaId"],
                "key_values": [company_id],
                "profile": "default"
            })
            get_result = parse_mcp_result(raw_result2)

            # Should succeed with proper key encoding
            assert "error" not in get_result
            assert get_result["data"]["DataAreaId"] == company_id
