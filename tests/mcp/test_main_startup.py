"""Tests for MCP server main startup functionality."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from d365fo_client.mcp.main import load_config
from d365fo_client.mcp import D365FOMCPServer


class TestLoadConfig:
    """Test the load_config function with different environment scenarios."""

    def test_load_config_no_environment_variables(self):
        """Test load_config with no environment variables (profile-only mode)."""
        with patch.dict(os.environ, {}, clear=True):
            config = load_config()
            
            assert config["startup_mode"] == "profile_only"
            assert config["has_base_url"] is False
            assert "default_environment" not in config

    def test_load_config_base_url_only(self):
        """Test load_config with only D365FO_BASE_URL (default auth mode)."""
        env_vars = {
            "D365FO_BASE_URL": "https://test.dynamics.com"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = load_config()
            
            assert config["startup_mode"] == "default_auth"
            assert config["has_base_url"] is True
            assert config["default_environment"]["base_url"] == "https://test.dynamics.com"
            assert config["default_environment"]["use_default_credentials"] is True

    def test_load_config_partial_credentials(self):
        """Test load_config with partial credentials falls back to default auth."""
        # Test with base URL and client ID only (missing secret and tenant)
        env_vars = {
            "D365FO_BASE_URL": "https://test.dynamics.com",
            "D365FO_CLIENT_ID": "test-client-id"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = load_config()
            
            assert config["startup_mode"] == "default_auth"
            assert config["has_base_url"] is True
            assert config["default_environment"]["base_url"] == "https://test.dynamics.com"
            assert config["default_environment"]["use_default_credentials"] is True

    def test_load_config_full_credentials(self):
        """Test load_config with full client credentials."""
        env_vars = {
            "D365FO_BASE_URL": "https://test.dynamics.com",
            "D365FO_CLIENT_ID": "test-client-id",
            "D365FO_CLIENT_SECRET": "test-client-secret",
            "D365FO_TENANT_ID": "test-tenant-id"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = load_config()
            
            assert config["startup_mode"] == "client_credentials"
            assert config["has_base_url"] is True
            assert config["default_environment"]["base_url"] == "https://test.dynamics.com"
            assert config["default_environment"]["client_id"] == "test-client-id"
            assert config["default_environment"]["client_secret"] == "test-client-secret"
            assert config["default_environment"]["tenant_id"] == "test-tenant-id"
            assert config["default_environment"]["use_default_credentials"] is False

    def test_load_config_missing_secret_only(self):
        """Test load_config with missing client secret only."""
        env_vars = {
            "D365FO_BASE_URL": "https://test.dynamics.com",
            "D365FO_CLIENT_ID": "test-client-id",
            "D365FO_TENANT_ID": "test-tenant-id"
            # Missing D365FO_CLIENT_SECRET
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = load_config()
            
            # Should fall back to default auth mode
            assert config["startup_mode"] == "default_auth"
            assert config["default_environment"]["use_default_credentials"] is True


class TestMCPServerStartup:
    """Test MCP server startup behavior with different configurations."""

    @pytest.mark.asyncio
    async def test_startup_profile_only_mode(self):
        """Test server startup in profile-only mode."""
        config = {
            "startup_mode": "profile_only",
            "has_base_url": False
        }
        
        with patch('d365fo_client.mcp.server.D365FOMCPServer._startup_health_checks') as mock_health_checks:
            with patch('d365fo_client.mcp.server.D365FOMCPServer._create_default_profile_if_needed') as mock_create_profile:
                server = D365FOMCPServer(config)
                await server._startup_initialization()
                
                # Should not perform health checks or create profiles in profile-only mode
                mock_health_checks.assert_not_called()
                mock_create_profile.assert_not_called()

    @pytest.mark.asyncio
    async def test_startup_default_auth_mode(self):
        """Test server startup in default authentication mode."""
        config = {
            "startup_mode": "default_auth",
            "has_base_url": True,
            "default_environment": {
                "base_url": "https://test.dynamics.com",
                "use_default_credentials": True
            }
        }
        
        with patch('d365fo_client.mcp.server.D365FOMCPServer._startup_health_checks') as mock_health_checks:
            with patch('d365fo_client.mcp.server.D365FOMCPServer._create_default_profile_if_needed') as mock_create_profile:
                mock_health_checks.return_value = None
                mock_create_profile.return_value = None
                
                server = D365FOMCPServer(config)
                await server._startup_initialization()
                
                # Should perform health checks and create profile
                mock_health_checks.assert_called_once()
                mock_create_profile.assert_called_once()

    @pytest.mark.asyncio
    async def test_startup_client_credentials_mode(self):
        """Test server startup in client credentials mode."""
        config = {
            "startup_mode": "client_credentials",
            "has_base_url": True,
            "default_environment": {
                "base_url": "https://test.dynamics.com",
                "client_id": "test-client-id",
                "client_secret": "test-client-secret",
                "tenant_id": "test-tenant-id",
                "use_default_credentials": False
            }
        }
        
        with patch('d365fo_client.mcp.server.D365FOMCPServer._startup_health_checks') as mock_health_checks:
            with patch('d365fo_client.mcp.server.D365FOMCPServer._create_default_profile_if_needed') as mock_create_profile:
                mock_health_checks.return_value = None
                mock_create_profile.return_value = None
                
                server = D365FOMCPServer(config)
                await server._startup_initialization()
                
                # Should perform health checks and create profile
                mock_health_checks.assert_called_once()
                mock_create_profile.assert_called_once()

    @pytest.mark.asyncio
    async def test_startup_initialization_handles_exceptions(self):
        """Test that startup initialization handles exceptions gracefully."""
        config = {
            "startup_mode": "default_auth",
            "has_base_url": True
        }
        
        with patch('d365fo_client.mcp.server.D365FOMCPServer._startup_health_checks') as mock_health_checks:
            # Simulate an exception during health checks
            mock_health_checks.side_effect = Exception("Health check failed")
            
            server = D365FOMCPServer(config)
            # Should not raise an exception - just log the error
            await server._startup_initialization()
            
            mock_health_checks.assert_called_once()


class TestCreateDefaultProfile:
    """Test default profile creation scenarios."""

    @pytest.mark.asyncio
    async def test_create_default_profile_default_auth_mode(self):
        """Test creating default profile in default auth mode."""
        config = {
            "startup_mode": "default_auth"
        }
        
        env_vars = {
            "D365FO_BASE_URL": "https://test.dynamics.com"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            # Mock ProfileManager at both the server and ProfileTools level
            mock_profile_manager = MagicMock()
            mock_profile_manager.get_default_profile.return_value = None
            mock_profile_manager.get_profile.return_value = None
            mock_profile_manager.create_profile.return_value = True
            
            with patch('d365fo_client.mcp.server.ProfileManager', return_value=mock_profile_manager):
                with patch('d365fo_client.mcp.tools.profile_tools.ProfileManager', return_value=mock_profile_manager):
                    server = D365FOMCPServer(config)
                    
                    await server._create_default_profile_if_needed()
                    
                    # Should create profile with default auth
                    mock_profile_manager.create_profile.assert_called_once()
                    call_args = mock_profile_manager.create_profile.call_args
                    assert call_args.kwargs["auth_mode"] == "default"
                    assert call_args.kwargs["base_url"] == "https://test.dynamics.com"
                    assert call_args.kwargs["client_id"] is None
                    assert call_args.kwargs["client_secret"] is None
                    assert call_args.kwargs["tenant_id"] is None
                    
                    # Should set as default
                    mock_profile_manager.set_default_profile.assert_called_once_with("default-from-env")

    @pytest.mark.asyncio
    async def test_create_default_profile_client_credentials_mode(self):
        """Test creating default profile in client credentials mode."""
        config = {
            "startup_mode": "client_credentials"
        }
        
        env_vars = {
            "D365FO_BASE_URL": "https://test.dynamics.com",
            "D365FO_CLIENT_ID": "test-client-id",
            "D365FO_CLIENT_SECRET": "test-client-secret",
            "D365FO_TENANT_ID": "test-tenant-id"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            # Mock ProfileManager at both the server and ProfileTools level
            mock_profile_manager = MagicMock()
            mock_profile_manager.get_default_profile.return_value = None
            mock_profile_manager.get_profile.return_value = None
            mock_profile_manager.create_profile.return_value = True
            
            with patch('d365fo_client.mcp.server.ProfileManager', return_value=mock_profile_manager):
                with patch('d365fo_client.mcp.tools.profile_tools.ProfileManager', return_value=mock_profile_manager):
                    server = D365FOMCPServer(config)
                    
                    await server._create_default_profile_if_needed()
                    
                    # Should create profile with client credentials auth
                    mock_profile_manager.create_profile.assert_called_once()
                    call_args = mock_profile_manager.create_profile.call_args
                    assert call_args.kwargs["auth_mode"] == "client_credentials"
                    assert call_args.kwargs["base_url"] == "https://test.dynamics.com"
                    assert call_args.kwargs["client_id"] == "test-client-id"
                    assert call_args.kwargs["client_secret"] == "test-client-secret"
                    assert call_args.kwargs["tenant_id"] == "test-tenant-id"

    @pytest.mark.asyncio
    async def test_create_default_profile_skips_if_exists(self):
        """Test that profile creation is skipped if default profile already exists."""
        config = {
            "startup_mode": "default_auth"
        }
        
        env_vars = {
            "D365FO_BASE_URL": "https://test.dynamics.com"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            # Mock ProfileManager at both the server and ProfileTools level
            mock_profile_manager = MagicMock()
            mock_existing_profile = MagicMock()
            mock_existing_profile.name = "existing-default"
            mock_profile_manager.get_default_profile.return_value = mock_existing_profile
            
            with patch('d365fo_client.mcp.server.ProfileManager', return_value=mock_profile_manager):
                with patch('d365fo_client.mcp.tools.profile_tools.ProfileManager', return_value=mock_profile_manager):
                    server = D365FOMCPServer(config)
                    
                    await server._create_default_profile_if_needed()
                    
                    # Should not create a new profile
                    mock_profile_manager.create_profile.assert_not_called()
                    mock_profile_manager.set_default_profile.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_default_profile_missing_credentials_in_client_mode(self):
        """Test profile creation fails gracefully when credentials are missing in client credentials mode."""
        config = {
            "startup_mode": "client_credentials"
        }
        
        env_vars = {
            "D365FO_BASE_URL": "https://test.dynamics.com",
            "D365FO_CLIENT_ID": "test-client-id"
            # Missing client_secret and tenant_id
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            # Mock ProfileManager at both the server and ProfileTools level
            mock_profile_manager = MagicMock()
            mock_profile_manager.get_default_profile.return_value = None
            
            with patch('d365fo_client.mcp.server.ProfileManager', return_value=mock_profile_manager):
                with patch('d365fo_client.mcp.tools.profile_tools.ProfileManager', return_value=mock_profile_manager):
                    server = D365FOMCPServer(config)
                    
                    await server._create_default_profile_if_needed()
                    
                    # Should not create profile due to missing credentials
                    mock_profile_manager.create_profile.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_default_profile_no_base_url(self):
        """Test profile creation is skipped when base URL is missing."""
        config = {
            "startup_mode": "default_auth"
        }
        
        with patch.dict(os.environ, {}, clear=True):
            # Mock ProfileManager at both the server and ProfileTools level
            mock_profile_manager = MagicMock()
            mock_profile_manager.get_default_profile.return_value = None
            
            with patch('d365fo_client.mcp.server.ProfileManager', return_value=mock_profile_manager):
                with patch('d365fo_client.mcp.tools.profile_tools.ProfileManager', return_value=mock_profile_manager):
                    server = D365FOMCPServer(config)
                    
                    await server._create_default_profile_if_needed()
                    
                    # Should not create profile due to missing base URL
                    mock_profile_manager.create_profile.assert_not_called()


class TestIntegrationScenarios:
    """Integration tests for complete startup scenarios."""

    @pytest.mark.asyncio
    async def test_end_to_end_profile_only_startup(self):
        """Test complete startup flow for profile-only mode."""
        with patch.dict(os.environ, {}, clear=True):
            config = load_config()
            
            with patch('d365fo_client.mcp.server.D365FOMCPServer._startup_health_checks') as mock_health_checks:
                with patch('d365fo_client.mcp.server.D365FOMCPServer._create_default_profile_if_needed') as mock_create_profile:
                    with patch('d365fo_client.mcp.server.ProfileManager'):
                        with patch('d365fo_client.mcp.tools.profile_tools.ProfileManager'):
                            server = D365FOMCPServer(config)
                            await server._startup_initialization()
                            
                            # Verify no initialization activities
                            mock_health_checks.assert_not_called()
                            mock_create_profile.assert_not_called()

    @pytest.mark.asyncio
    async def test_end_to_end_default_auth_startup(self):
        """Test complete startup flow for default auth mode."""
        env_vars = {
            "D365FO_BASE_URL": "https://test.dynamics.com"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = load_config()
            
            with patch('d365fo_client.mcp.server.D365FOMCPServer._startup_health_checks') as mock_health_checks:
                with patch('d365fo_client.mcp.server.D365FOMCPServer._create_default_profile_if_needed') as mock_create_profile:
                    with patch('d365fo_client.mcp.server.ProfileManager'):
                        with patch('d365fo_client.mcp.tools.profile_tools.ProfileManager'):
                            mock_health_checks.return_value = None
                            mock_create_profile.return_value = None
                            
                            server = D365FOMCPServer(config)
                            await server._startup_initialization()
                            
                            # Verify startup activities
                            mock_health_checks.assert_called_once()
                            mock_create_profile.assert_called_once()

    @pytest.mark.asyncio
    async def test_end_to_end_client_credentials_startup(self):
        """Test complete startup flow for client credentials mode."""
        env_vars = {
            "D365FO_BASE_URL": "https://test.dynamics.com",
            "D365FO_CLIENT_ID": "test-client-id",
            "D365FO_CLIENT_SECRET": "test-client-secret",
            "D365FO_TENANT_ID": "test-tenant-id"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = load_config()
            
            with patch('d365fo_client.mcp.server.D365FOMCPServer._startup_health_checks') as mock_health_checks:
                with patch('d365fo_client.mcp.server.D365FOMCPServer._create_default_profile_if_needed') as mock_create_profile:
                    with patch('d365fo_client.mcp.server.ProfileManager'):
                        with patch('d365fo_client.mcp.tools.profile_tools.ProfileManager'):
                            mock_health_checks.return_value = None
                            mock_create_profile.return_value = None
                            
                            server = D365FOMCPServer(config)
                            await server._startup_initialization()
                            
                            # Verify startup activities
                            mock_health_checks.assert_called_once()
                            mock_create_profile.assert_called_once()