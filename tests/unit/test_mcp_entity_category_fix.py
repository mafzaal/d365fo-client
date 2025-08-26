"""Integration test for the entity_category fix in MCP metadata tools."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from d365fo_client.mcp.tools.metadata_tools import MetadataTools
from d365fo_client.models import DataEntityInfo, EntityCategory


@pytest.mark.asyncio
async def test_mcp_search_entities_with_mixed_entity_categories():
    """Test MCP search entities tool with both string and enum entity_category values."""
    
    # Create a mock client manager
    client_manager = MagicMock()
    
    # Create a mock client
    mock_client = AsyncMock()
    client_manager.get_client = AsyncMock(return_value=mock_client)
    
    # Mock entities with mixed entity_category types
    entities = [
        # Entity with string entity_category (the problematic case)
        DataEntityInfo(
            name="SrsFinanceCopilotEntity", 
            public_entity_name="SrsFinanceCopilot",
            public_collection_name="SrsFinanceCopilots",
            label_id="@SRS123456",
            label_text="Finance Copilot Entity",
            data_service_enabled=True,
            data_management_enabled=True,
            entity_category="Transaction",  # String value
            is_read_only=False
        ),
        # Entity with enum entity_category (the correct case)
        DataEntityInfo(
            name="CustomerEntity",
            public_entity_name="Customer", 
            public_collection_name="Customers",
            label_id="@CUS789",
            label_text="Customer Entity",
            data_service_enabled=True,
            data_management_enabled=True,
            entity_category=EntityCategory.MASTER,  # Enum value
            is_read_only=False
        ),
        # Entity with None entity_category
        DataEntityInfo(
            name="GenericEntity",
            public_entity_name="Generic",
            public_collection_name="Generics",
            label_id="@GEN999",
            label_text="Generic Entity",
            data_service_enabled=False,
            data_management_enabled=True,
            entity_category=None,  # None value
            is_read_only=True
        )
    ]
    
    mock_client.search_data_entities = AsyncMock(return_value=entities)
    mock_client.metadata_cache = None  # No cache for simpler test
    
    # Create metadata tools instance
    metadata_tools = MetadataTools(client_manager)
    
    # Test arguments
    arguments = {
        "pattern": "Entity",
        "profile": "onebox"
    }
    
    # Execute the search
    result = await metadata_tools.execute_search_entities(arguments)
    
    # Parse the result
    assert len(result) == 1
    response = json.loads(result[0].text)
    
    # Verify successful execution (no error field)
    assert "error" not in response
    assert "entities" in response
    assert len(response["entities"]) == 3
    
    # Verify entity_category handling
    entities_data = response["entities"]
    
    # String entity_category should be preserved
    assert entities_data[0]["entity_category"] == "Transaction"
    assert entities_data[0]["name"] == "SrsFinanceCopilotEntity"
    
    # Enum entity_category should be converted to string value
    assert entities_data[1]["entity_category"] == "Master"
    assert entities_data[1]["name"] == "CustomerEntity"
    
    # None entity_category should remain None
    assert entities_data[2]["entity_category"] is None
    assert entities_data[2]["name"] == "GenericEntity"
    
    # Verify other response fields
    assert response["totalCount"] == 3
    assert response["returnedCount"] == 3
    assert response["pattern"] == "Entity"


if __name__ == "__main__":
    asyncio.run(test_mcp_search_entities_with_mixed_entity_categories())