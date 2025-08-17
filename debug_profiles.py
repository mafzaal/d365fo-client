#!/usr/bin/env python3
"""Debug profile configuration for MCP server."""

import asyncio
from d365fo_client.profile_manager import ProfileManager
from d365fo_client.mcp.client_manager import D365FOClientManager

async def main():
    print("=== Profile Debug ===")
    
    # Check profile manager
    pm = ProfileManager()
    
    print("\nAvailable profiles:")
    profiles = pm.list_profiles()
    for name, profile in profiles.items():
        print(f"  {name}: {profile.base_url} ({profile.auth_mode})")
    
    default_profile = pm.get_default_profile()
    print(f"\nDefault profile: {default_profile.name if default_profile else 'None'}")
    
    effective_default = pm.get_effective_profile("default")
    print(f"Effective profile for 'default': {effective_default.name if effective_default else 'None'}")
    
    effective_none = pm.get_effective_profile(None)
    print(f"Effective profile for None: {effective_none.name if effective_none else 'None'}")
    
    # Test client manager
    print("\n=== Client Manager Debug ===")
    
    config = {
        "default_environment": {
            "base_url": "https://usnconeboxax1aos.cloud.onebox.dynamics.com",
            "use_default_credentials": True,
            "timeout": 60,
            "verify_ssl": True,
            "use_label_cache": True
        },
        "profiles": {
            "default": {
                "base_url": "https://usnconeboxax1aos.cloud.onebox.dynamics.com",
                "use_default_credentials": True
            }
        }
    }
    
    client_manager = D365FOClientManager(config)
    
    try:
        client_config = client_manager._build_client_config("default")
        print(f"\nClient config for 'default' profile:")
        print(f"  base_url: {client_config.base_url}")
        print(f"  use_default_credentials: {client_config.use_default_credentials}")
        print(f"  client_id: {client_config.client_id}")
        
        if client_config.base_url is None:
            print("ERROR: base_url is None!")
        else:
            print("SUCCESS: base_url is configured")
            
        # Test actual connection
        print("\n=== Testing Connection ===")
        success = await client_manager.test_connection("default")
        print(f"Connection test result: {success}")
        
    except Exception as e:
        print(f"Error building client config: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())