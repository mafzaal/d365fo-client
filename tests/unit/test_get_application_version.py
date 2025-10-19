"""Unit tests for GetApplicationVersion action method.

These tests validate the get_application_version() method logic using mocks,
ensuring proper response handling and error management without external dependencies.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from d365fo_client import FOClient, FOClientConfig
from d365fo_client.exceptions import FOClientError


@pytest.mark.asyncio
async def test_get_application_version_success():
    """Test successful GetApplicationVersion action call"""
    config = FOClientConfig(base_url="https://test.dynamics.com")

    with (
        patch("d365fo_client.auth.DefaultAzureCredential"),
        patch("d365fo_client.session.SessionManager") as mock_session_manager_class,
        patch.object(FOClient, "call_action") as mock_call,
    ):
        # Mock the session manager
        mock_session_manager = AsyncMock()
        mock_session_manager_class.return_value = mock_session_manager

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

    with (
        patch("d365fo_client.auth.DefaultAzureCredential"),
        patch("d365fo_client.session.SessionManager") as mock_session_manager_class,
        patch.object(FOClient, "call_action") as mock_call,
    ):
        # Mock the session manager
        mock_session_manager = AsyncMock()
        mock_session_manager_class.return_value = mock_session_manager

        mock_call.return_value = {"value": "10.0.1985.137"}

        async with FOClient(config) as client:
            result = await client.get_application_version()

            assert result == "10.0.1985.137"


@pytest.mark.asyncio
async def test_get_application_version_other_response():
    """Test GetApplicationVersion action call with other response types"""
    config = FOClientConfig(base_url="https://test.dynamics.com")

    # Test with number response
    with (
        patch("d365fo_client.auth.DefaultAzureCredential"),
        patch("d365fo_client.session.SessionManager") as mock_session_manager_class,
        patch.object(FOClient, "call_action") as mock_call,
    ):
        # Mock the session manager
        mock_session_manager = AsyncMock()
        mock_session_manager_class.return_value = mock_session_manager

        mock_call.return_value = 123

        async with FOClient(config) as client:
            result = await client.get_application_version()

            assert result == "123"

    # Test with None response
    with (
        patch("d365fo_client.auth.DefaultAzureCredential"),
        patch("d365fo_client.session.SessionManager") as mock_session_manager_class,
        patch.object(FOClient, "call_action") as mock_call,
    ):
        # Mock the session manager
        mock_session_manager = AsyncMock()
        mock_session_manager_class.return_value = mock_session_manager

        mock_call.return_value = None

        async with FOClient(config) as client:
            result = await client.get_application_version()

            assert result == ""


@pytest.mark.asyncio
async def test_get_application_version_error():
    """Test GetApplicationVersion action call error handling"""
    config = FOClientConfig(base_url="https://test.dynamics.com")

    with (
        patch("d365fo_client.auth.DefaultAzureCredential"),
        patch("d365fo_client.session.SessionManager") as mock_session_manager_class,
        patch.object(FOClient, "call_action") as mock_call,
    ):
        # Mock the session manager
        mock_session_manager = AsyncMock()
        mock_session_manager_class.return_value = mock_session_manager

        mock_call.side_effect = Exception("Action failed")

        async with FOClient(config) as client:
            with pytest.raises(
                FOClientError, match="Failed to get application version"
            ):
                await client.get_application_version()


