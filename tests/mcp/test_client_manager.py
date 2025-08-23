"""Tests for MCP client manager functionality."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from d365fo_client.mcp import D365FOClientManager


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
                "use_default_credentials": True,
            },
            "profiles": {
                "test": {"base_url": "https://test.dynamics.com", "timeout": 120}
            },
        }

        manager = D365FOClientManager(config)

        # Test default profile
        default_config = manager._build_client_config("default")
        assert (
            default_config.base_url
            == "https://usnconeboxax1aos.cloud.onebox.dynamics.com"
        )
        assert default_config.use_default_credentials is True

        # Test specific profile
        test_config = manager._build_client_config("test")
        assert test_config.base_url == "https://test.dynamics.com"
        assert test_config.timeout == 120
        assert test_config.use_default_credentials is True  # Inherited from default
