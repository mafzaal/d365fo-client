"""Tests for GetApplicationVersion action method."""

from unittest.mock import AsyncMock, patch

import pytest

from d365fo_client import FOClient, FOClientConfig
from d365fo_client.exceptions import FOClientError


@pytest.mark.asyncio
async def test_get_application_version_success():
    """Test successful GetApplicationVersion action call"""
    config = FOClientConfig(base_url="https://test.dynamics.com")

    with patch.object(FOClient, "call_action") as mock_call:
        mock_call.return_value = "10.0.1985.137"

        async with FOClient(config) as client:
            result = await client.get_application_version()

            assert result == "10.0.1985.137"

            mock_call.assert_called_once_with(
                "GetApplicationVersion",
                parameters=None,
                entity_name="DataManagementEntities",
            )


@pytest.mark.asyncio
async def test_get_application_version_dict_response():
    """Test GetApplicationVersion action call with dict response containing value"""
    config = FOClientConfig(base_url="https://test.dynamics.com")

    with patch.object(FOClient, "call_action") as mock_call:
        mock_call.return_value = {"value": "10.0.1985.137"}

        async with FOClient(config) as client:
            result = await client.get_application_version()

            assert result == "10.0.1985.137"


@pytest.mark.asyncio
async def test_get_application_version_other_response():
    """Test GetApplicationVersion action call with other response types"""
    config = FOClientConfig(base_url="https://test.dynamics.com")

    # Test with number response
    with patch.object(FOClient, "call_action") as mock_call:
        mock_call.return_value = 123

        async with FOClient(config) as client:
            result = await client.get_application_version()

            assert result == "123"

    # Test with None response
    with patch.object(FOClient, "call_action") as mock_call:
        mock_call.return_value = None

        async with FOClient(config) as client:
            result = await client.get_application_version()

            assert result == ""


@pytest.mark.asyncio
async def test_get_application_version_error():
    """Test GetApplicationVersion action call error handling"""
    config = FOClientConfig(base_url="https://test.dynamics.com")

    with patch.object(FOClient, "call_action") as mock_call:
        mock_call.side_effect = Exception("Action failed")

        async with FOClient(config) as client:
            with pytest.raises(
                FOClientError, match="Failed to get application version"
            ):
                await client.get_application_version()


@pytest.mark.asyncio
async def test_get_application_version_integration():
    """Integration test for GetApplicationVersion action (requires live connection)"""
    # This test would require actual F&O credentials and connection
    # Uncomment and configure if you want to test against a real environment

    # config = FOClientConfig(
    #     base_url="https://your-d365.dynamics.com",
    #     use_default_credentials=True,
    #     verify_ssl=False
    # )
    #
    # async with FOClient(config) as client:
    #     version = await client.get_application_version()
    #
    #     # Verify the result is a non-empty string
    #     assert isinstance(version, str)
    #     assert len(version) > 0
    #     print(f"Application version: {version}")

    # Skip this test unless explicitly enabled
    pytest.skip("Integration test requires live F&O connection")
