"""Tests for MCP resource handlers."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from d365fo_client.mcp.resources import (
    EntityResourceHandler,
    EnvironmentResourceHandler,
)


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
        mock_client = AsyncMock()  # Use AsyncMock for async search_entities method
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


class TestEnvironmentResourceHandler:
    """Test environment resource handler."""

    def test_init(self):
        """Test environment resource handler initialization."""
        client_manager = MagicMock()
        handler = EnvironmentResourceHandler(client_manager)

        assert handler.client_manager == client_manager
