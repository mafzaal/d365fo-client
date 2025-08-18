#!/usr/bin/env python3
"""
Example script demonstrating the new enumeration tools in the d365fo-client MCP server.

This script shows how to:
1. Search for enumerations by pattern
2. Get detailed enumeration field information including members and their values

Prerequisites:
- d365fo-client package installed
- D365 Finance & Operations environment access
- Proper authentication configuration

Usage:
    python examples/enumeration_tools_example.py

Environment Variables:
    D365FO_BASE_URL: Base URL of your D365 F&O environment
    AZURE_CLIENT_ID: Azure AD Client ID (if not using default credentials)
    AZURE_CLIENT_SECRET: Azure AD Client Secret (if not using default credentials)
    AZURE_TENANT_ID: Azure AD Tenant ID (if not using default credentials)
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from d365fo_client.mcp.tools.metadata_tools import MetadataTools
from d365fo_client.mcp.client_manager import D365FOClientManager


async def demonstrate_enumeration_tools():
    """Demonstrate the enumeration tools with real D365FO connection."""
    
    print("D365 Finance & Operations - Enumeration Tools Example")
    print("=" * 60)
    
    # Configuration for D365FO connection
    config = {
        "default": {
            "base_url": os.getenv('D365FO_BASE_URL', 'https://usnconeboxax1aos.cloud.onebox.dynamics.com'),
            "use_default_credentials": True,
            "use_label_cache": True
        }
    }
    
    try:
        # Initialize tools
        client_manager = D365FOClientManager(config)
        metadata_tools = MetadataTools(client_manager)
        
        print(f"Connecting to: {config['default']['base_url']}")
        print()
        
        # Example 1: Search for enumerations with "status" pattern
        print("1. Searching for enumerations containing 'status'...")
        print("-" * 50)
        
        search_args = {
            "pattern": ".*[Ss]tatus.*",
            "limit": 5
        }
        
        search_results = await metadata_tools.execute_search_enumerations(search_args)
        search_response = json.loads(search_results[0].text)
        
        print(f"Search pattern: {search_response['pattern']}")
        print(f"Found {search_response['totalCount']} enumerations (showing {len(search_response['enumerations'])})")
        print(f"Search time: {search_response['searchTime']}s")
        print()
        
        for i, enum in enumerate(search_response['enumerations'], 1):
            print(f"{i}. {enum['name']}")
            if enum.get('label_text'):
                print(f"   Label: {enum['label_text']}")
            print(f"   Members: {len(enum.get('members', []))}")
            print()
        
        # Example 2: Get detailed information for a specific enumeration
        if search_response['enumerations']:
            first_enum = search_response['enumerations'][0]
            enum_name = first_enum['name']
            
            print(f"2. Getting detailed information for '{enum_name}'...")
            print("-" * 50)
            
            fields_args = {
                "enumeration_name": enum_name,
                "resolve_labels": True,
                "language": "en-US"
            }
            
            fields_results = await metadata_tools.execute_get_enumeration_fields(fields_args)
            fields_response = json.loads(fields_results[0].text)
            
            enum_info = fields_response['enumeration']
            
            print(f"Enumeration: {enum_info['name']}")
            if enum_info.get('label_text'):
                print(f"Label: {enum_info['label_text']}")
            print(f"Total members: {fields_response['memberCount']}")
            print(f"Has labels: {fields_response['hasLabels']}")
            print()
            
            if enum_info.get('members'):
                print("Members:")
                for member in enum_info['members']:
                    print(f"  - {member['name']} = {member['value']}")
                    if member.get('label_text'):
                        print(f"    Label: {member['label_text']}")
                    print()
            
        # Example 3: Search for specific enumeration types
        print("3. Searching for currency-related enumerations...")
        print("-" * 50)
        
        currency_args = {
            "pattern": ".*[Cc]urrency.*",
            "limit": 3
        }
        
        currency_results = await metadata_tools.execute_search_enumerations(currency_args)
        currency_response = json.loads(currency_results[0].text)
        
        print(f"Found {currency_response['totalCount']} currency-related enumerations:")
        for enum in currency_response['enumerations']:
            print(f"  - {enum['name']}")
            if enum.get('label_text'):
                print(f"    {enum['label_text']}")
        print()
        
        # Example 4: Demonstrate error handling
        print("4. Testing error handling with invalid enumeration...")
        print("-" * 50)
        
        invalid_args = {
            "enumeration_name": "NonExistentEnumeration123456"
        }
        
        try:
            error_results = await metadata_tools.execute_get_enumeration_fields(invalid_args)
            error_response = json.loads(error_results[0].text)
            
            if 'error' in error_response:
                print(f"✓ Error properly handled: {error_response['error']}")
            else:
                print("Unexpected: No error for invalid enumeration")
        except Exception as e:
            print(f"✓ Exception properly caught: {e}")
        
        print()
        print("✓ Enumeration tools demonstration completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure you have:")
        print("1. Valid D365FO environment URL")
        print("2. Proper authentication configured")
        print("3. Network connectivity to D365FO")
        sys.exit(1)


async def show_tool_schemas():
    """Show the JSON schemas for the enumeration tools."""
    
    print("Enumeration Tools - JSON Schemas")
    print("=" * 40)
    
    client_manager = D365FOClientManager({})
    metadata_tools = MetadataTools(client_manager)
    tools = metadata_tools.get_tools()
    
    # Find enumeration tools
    enum_tools = [tool for tool in tools if 'enumeration' in tool.name]
    
    for tool in enum_tools:
        print(f"\nTool: {tool.name}")
        print(f"Description: {tool.description}")
        print("Input Schema:")
        print(json.dumps(tool.inputSchema, indent=2))
        print("-" * 40)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="D365FO Enumeration Tools Example")
    parser.add_argument("--schemas-only", action="store_true", 
                       help="Show tool schemas only (no D365FO connection)")
    
    args = parser.parse_args()
    
    if args.schemas_only:
        asyncio.run(show_tool_schemas())
    else:
        asyncio.run(demonstrate_enumeration_tools())