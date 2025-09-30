"""Tests for MCP client manager functionality."""


from typing import Optional
from unittest.mock import AsyncMock, MagicMock

import pytest

from d365fo_client.mcp import D365FOClientManager
from d365fo_client.models import FOClientConfig
from d365fo_client.profile_manager import ProfileManager
from d365fo_client.profiles import Profile


class TestD365FOClientManager:
    """Test D365FO client manager."""

    def test_init(self):
        """Test client manager initialization."""
        config = {"default_environment": {"base_url": "https://test.dynamics.com"}}
        manager = D365FOClientManager()


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


        manager = D365FOClientManager()

        # Test default profile
        default_config:Optional[FOClientConfig] = manager._build_client_config("default")
        assert default_config is not None
        assert (
            default_config.base_url
            == "https://usnconeboxax1aos.cloud.onebox.dynamics.com"
        )


        # Test specific profile
        test_config = manager._build_client_config("test")
        assert test_config is not None
        assert test_config.base_url == "https://test.dynamics.com"
        assert test_config.timeout == 120

