#!/usr/bin/env python3
"""
Simple D365 F&O Connection Test with Headers Display

This is a minimal test script that:
1. Tests connection to D365 Finance & Operations
2. Displays all HTTP response headers from the server
3. Shows authentication and connection status

Usage:
    python simple_connection_test.py

Environment Variables (optional):
    D365FO_BASE_URL - D365 F&O environment URL
    AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID - Azure AD credentials
"""

import asyncio
import os
import sys
from typing import Dict, List, Tuple

# Add the src directory to Python path for local development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from d365fo_client import FOClient, FOClientConfig


async def test_connection_and_show_headers() -> bool:
    """Test D365 F&O connection and display response headers."""
    
    print("🔧 D365 F&O Connection & Headers Test")
    print("=" * 45)
    
    # Configuration
    base_url = os.getenv('D365FO_BASE_URL', 'https://usnconeboxax1aos.cloud.onebox.dynamics.com')
    print(f"📍 Target URL: {base_url}")
    
    config = FOClientConfig(
        base_url=base_url,
        use_default_credentials=True,
        use_label_cache=False
    )
    
    client = None
    
    try:
        # Create and test client
        print("🔌 Connecting to D365 F&O...")
        client = FOClient(config=config)
        
        # Test basic connectivity
        app_version = await client.get_application_version()
        print(f"✅ Connected successfully! Version: {app_version}")
        print()
        
        # Get detailed headers from a simple endpoint
        session = await client.session_manager.get_session()
        test_url = f"{base_url}/data"
        
        print("📋 HTTP Response Headers:")
        print("-" * 30)
        
        async with session.get(test_url) as response:
            # Display all headers in a clean format
            headers = list(response.headers.items())
            
            # Sort headers for consistent display
            headers.sort(key=lambda x: x[0].lower())
            
            for name, value in headers:
                # Truncate very long header values for readability
                display_value = value if len(value) <= 100 else f"{value[:97]}..."
                print(f"{name}: {display_value}")
            
            print()
            print(f"📊 Status: {response.status} {response.reason}")
            print(f"📋 Header Count: {len(headers)}")
        
        # Identify D365 F&O specific headers
        print()
        print("🏢 D365 F&O Specific Headers:")
        print("-" * 35)
        
        d365_headers = []
        for name, value in headers:
            name_lower = name.lower()
            if any(keyword in name_lower for keyword in ['ms-dyn', 'odata', 'dynamics', 'x-ms']):
                d365_headers.append((name, value))
        
        if d365_headers:
            for name, value in d365_headers:
                display_value = value if len(value) <= 80 else f"{value[:77]}..."
                print(f"  {name}: {display_value}")
        else:
            print("  No D365-specific headers found")
        
        print()
        print("🎉 Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print()
        print("💡 Troubleshooting:")
        print(f"   • Check URL: {base_url}")
        print("   • Verify authentication (Azure AD default credentials)")
        print("   • Ensure network connectivity")
        print("   • Check firewall/proxy settings")
        return False
        
    finally:
        # Clean up
        if client:
            try:
                await client.session_manager.close()
            except:
                pass


def show_environment():
    """Display current environment configuration."""
    print("🌍 Environment Configuration:")
    print("-" * 30)
    
    env_vars = {
        'D365FO_BASE_URL': os.getenv('D365FO_BASE_URL', 'Not set'),
        'AZURE_CLIENT_ID': os.getenv('AZURE_CLIENT_ID', 'Not set'),
        'AZURE_CLIENT_SECRET': '***' if os.getenv('AZURE_CLIENT_SECRET') else 'Not set',
        'AZURE_TENANT_ID': os.getenv('AZURE_TENANT_ID', 'Not set')
    }
    
    for key, value in env_vars.items():
        print(f"{key}: {value}")
    
    print()


async def main():
    """Main entry point."""
    show_environment()
    success = await test_connection_and_show_headers()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)