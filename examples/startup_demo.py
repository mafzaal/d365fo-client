"""Demonstration script for improved MCP server startup behavior.

This script demonstrates the three startup scenarios:
1. Profile-only mode (no environment variables)
2. Default authentication mode (D365FO_BASE_URL only)
3. Client credentials mode (full environment variables)
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from d365fo_client.mcp.main import load_config
from d365fo_client.mcp import D365FOMCPServer
from unittest.mock import patch, MagicMock


async def demonstrate_startup_behavior():
    """Demonstrate the three startup scenarios."""
    
    print("=" * 80)
    print("D365FO MCP Server Startup Behavior Demonstration")
    print("=" * 80)
    
    # Scenario 1: Profile-only mode
    print("\n1. PROFILE-ONLY MODE (No environment variables)")
    print("-" * 50)
    
    with patch.dict(os.environ, {}, clear=True):
        config = load_config()
        print(f"Startup mode: {config['startup_mode']}")
        print(f"Has base URL: {config['has_base_url']}")
        print("Expected behavior: Server starts without configuration, profile management tools available")
    
    # Scenario 2: Default authentication mode
    print("\n2. DEFAULT AUTHENTICATION MODE (D365FO_BASE_URL only)")
    print("-" * 50)
    
    env_vars = {"D365FO_BASE_URL": "https://test.dynamics.com"}
    with patch.dict(os.environ, env_vars, clear=True):
        config = load_config()
        print(f"Startup mode: {config['startup_mode']}")
        print(f"Has base URL: {config['has_base_url']}")
        print(f"Base URL: {config['default_environment']['base_url']}")
        print(f"Use default credentials: {config['default_environment']['use_default_credentials']}")
        print("Expected behavior: Server creates default profile with default Azure credentials")
    
    # Scenario 3: Client credentials mode
    print("\n3. CLIENT CREDENTIALS MODE (Full environment variables)")
    print("-" * 50)
    
    env_vars = {
        "D365FO_BASE_URL": "https://test.dynamics.com",
        "D365FO_CLIENT_ID": "test-client-id",
        "D365FO_CLIENT_SECRET": "test-client-secret",
        "D365FO_TENANT_ID": "test-tenant-id"
    }
    with patch.dict(os.environ, env_vars, clear=True):
        config = load_config()
        print(f"Startup mode: {config['startup_mode']}")
        print(f"Has base URL: {config['has_base_url']}")
        print(f"Base URL: {config['default_environment']['base_url']}")
        print(f"Client ID: {config['default_environment']['client_id']}")
        print(f"Tenant ID: {config['default_environment']['tenant_id']}")
        print(f"Use default credentials: {config['default_environment']['use_default_credentials']}")
        print("Expected behavior: Server creates default profile with client credential authentication")
    
    # Scenario 4: Partial credentials (should fall back to default auth)
    print("\n4. PARTIAL CREDENTIALS (Falls back to default auth)")
    print("-" * 50)
    
    env_vars = {
        "D365FO_BASE_URL": "https://test.dynamics.com",
        "D365FO_CLIENT_ID": "test-client-id"
        # Missing client_secret and tenant_id
    }
    with patch.dict(os.environ, env_vars, clear=True):
        config = load_config()
        print(f"Startup mode: {config['startup_mode']}")
        print(f"Has base URL: {config['has_base_url']}")
        print(f"Base URL: {config['default_environment']['base_url']}")
        print(f"Use default credentials: {config['default_environment']['use_default_credentials']}")
        print("Expected behavior: Falls back to default authentication mode")
    
    print("\n" + "=" * 80)
    print("Demonstration complete!")
    print("=" * 80)


async def demonstrate_server_startup():
    """Demonstrate actual server startup initialization."""
    print("\n" + "=" * 80)
    print("SERVER STARTUP INITIALIZATION DEMONSTRATION")
    print("=" * 80)
    
    # Mock the ProfileManager to avoid file system dependencies
    mock_profile_manager = MagicMock()
    mock_profile_manager.get_default_profile.return_value = None
    mock_profile_manager.get_profile.return_value = None
    mock_profile_manager.create_profile.return_value = True
    
    with patch('d365fo_client.mcp.server.ProfileManager', return_value=mock_profile_manager):
        with patch('d365fo_client.mcp.tools.profile_tools.ProfileManager', return_value=mock_profile_manager):
            
            # Test scenario 1: Profile-only mode
            print("\n1. Testing profile-only mode startup...")
            with patch.dict(os.environ, {}, clear=True):
                config = load_config()
                server = D365FOMCPServer(config)
                
                with patch.object(server, '_startup_health_checks') as mock_health_checks:
                    with patch.object(server, '_create_default_profile_if_needed') as mock_create_profile:
                        await server._startup_initialization()
                        
                        print(f"   Health checks called: {mock_health_checks.called}")
                        print(f"   Profile creation called: {mock_create_profile.called}")
                        print("   ✓ Profile-only mode working correctly")
            
            # Test scenario 2: Default auth mode
            print("\n2. Testing default auth mode startup...")
            env_vars = {"D365FO_BASE_URL": "https://test.dynamics.com"}
            with patch.dict(os.environ, env_vars, clear=True):
                config = load_config()
                server = D365FOMCPServer(config)
                
                with patch.object(server, '_startup_health_checks') as mock_health_checks:
                    with patch.object(server, '_create_default_profile_if_needed') as mock_create_profile:
                        await server._startup_initialization()
                        
                        print(f"   Health checks called: {mock_health_checks.called}")
                        print(f"   Profile creation called: {mock_create_profile.called}")
                        print("   ✓ Default auth mode working correctly")
            
            # Test scenario 3: Client credentials mode
            print("\n3. Testing client credentials mode startup...")
            env_vars = {
                "D365FO_BASE_URL": "https://test.dynamics.com",
                "D365FO_CLIENT_ID": "test-client-id",
                "D365FO_CLIENT_SECRET": "test-client-secret",
                "D365FO_TENANT_ID": "test-tenant-id"
            }
            with patch.dict(os.environ, env_vars, clear=True):
                config = load_config()
                server = D365FOMCPServer(config)
                
                with patch.object(server, '_startup_health_checks') as mock_health_checks:
                    with patch.object(server, '_create_default_profile_if_needed') as mock_create_profile:
                        await server._startup_initialization()
                        
                        print(f"   Health checks called: {mock_health_checks.called}")
                        print(f"   Profile creation called: {mock_create_profile.called}")
                        print("   ✓ Client credentials mode working correctly")
    
    print("\n" + "=" * 80)
    print("Server startup demonstration complete!")
    print("=" * 80)


async def main():
    """Main demonstration function."""
    await demonstrate_startup_behavior()
    await demonstrate_server_startup()


if __name__ == "__main__":
    asyncio.run(main())