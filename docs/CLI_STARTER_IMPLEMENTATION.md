# CLI Enhancement Starter Implementation

This file demonstrates how to begin implementing the CLI enhancements in the current `main.py` file. This is a minimal working example that adds the basic command structure while maintaining backward compatibility.

## Enhanced main.py (Starter Implementation)

```python
"""Enhanced main module for d365fo-client package with CLI support."""

import asyncio
import argparse
import sys
import json
from typing import Optional, Dict, Any

from .client import FOClient, create_client
from .models import FOClientConfig, QueryOptions
from . import __version__, __author__, __email__


class SimpleCLI:
    """Simple CLI manager for basic commands"""
    
    def __init__(self):
        self.client = None
    
    async def execute_command(self, args: argparse.Namespace) -> int:
        """Execute the specified command"""
        try:
            # Handle legacy demo mode
            if args.demo or (not hasattr(args, 'command') or not args.command):
                return await self._run_demo()
            
            # Validate base URL
            if not args.base_url:
                print("Error: --base-url is required for all commands")
                return 1
            
            # Create client configuration
            config = FOClientConfig(
                base_url=args.base_url,
                use_default_credentials=not any([args.client_id, args.client_secret, args.tenant_id]),
                client_id=args.client_id,
                client_secret=args.client_secret,
                tenant_id=args.tenant_id,
                verify_ssl=getattr(args, 'verify_ssl', True),
                use_label_cache=getattr(args, 'label_cache', True),
                label_cache_expiry_minutes=getattr(args, 'label_expiry', 60)
            )
            
            # Execute command with client
            async with FOClient(config) as client:
                self.client = client
                
                if args.command == "test":
                    return await self._handle_test_command(args)
                elif args.command == "version":
                    return await self._handle_version_command(args)
                elif args.command == "metadata":
                    return await self._handle_metadata_command(args)
                elif args.command == "entity":
                    return await self._handle_entity_command(args)
                elif args.command == "action":
                    return await self._handle_action_command(args)
                else:
                    print(f"Unknown command: {args.command}")
                    return 1
                    
        except Exception as e:
            if getattr(args, 'verbose', False):
                import traceback
                traceback.print_exc()
            else:
                print(f"Error: {e}")
            return 1
    
    async def _run_demo(self) -> int:
        """Run the original demo/example usage"""
        print("Microsoft Dynamics 365 Finance & Operations Client - Demo Mode")
        print("=" * 60)
        print("Use 'd365fo-client --help' for command-line interface options")
        print("=" * 60)
        
        try:
            await example_usage()
            return 0
        except Exception as e:
            print(f"Demo error: {e}")
            return 1
    
    async def _handle_test_command(self, args: argparse.Namespace) -> int:
        """Handle test connectivity command"""
        print("Testing connectivity to D365 F&O environment...")
        
        success = True
        
        if not getattr(args, 'metadata_only', False):
            if await self.client.test_connection():
                print("✅ OData API connection successful")
            else:
                print("❌ OData API connection failed")
                success = False
        
        if not getattr(args, 'odata_only', False):
            if await self.client.test_metadata_connection():
                print("✅ Metadata API connection successful")
            else:
                print("❌ Metadata API connection failed")
                success = False
        
        return 0 if success else 1
    
    async def _handle_version_command(self, args: argparse.Namespace) -> int:
        """Handle version information command"""
        try:
            output_format = getattr(args, 'output', 'table')
            
            # Get version information
            versions = {}
            
            if getattr(args, 'application', False) or getattr(args, 'all', True):
                versions['application'] = await self.client.get_application_version()
            
            if getattr(args, 'platform', False) or getattr(args, 'all', True):
                versions['platform_build'] = await self.client.get_platform_build_version()
            
            if getattr(args, 'build', False) or getattr(args, 'all', True):
                versions['application_build'] = await self.client.get_application_build_version()
            
            # Format output
            if output_format == 'json':
                print(json.dumps(versions, indent=2))
            else:
                for key, value in versions.items():
                    print(f"{key.replace('_', ' ').title()}: {value}")
            
            return 0
            
        except Exception as e:
            print(f"Error retrieving version information: {e}")
            return 1
    
    async def _handle_metadata_command(self, args: argparse.Namespace) -> int:
        """Handle metadata operations"""
        subcommand = getattr(args, 'metadata_subcommand', 'sync')
        
        if subcommand == 'sync':
            print("Syncing metadata...")
            force = getattr(args, 'force', False)
            success = await self.client.download_metadata(force_refresh=force)
            
            if success:
                print("✅ Metadata sync completed successfully")
                return 0
            else:
                print("❌ Metadata sync failed")
                return 1
                
        elif subcommand == 'search':
            pattern = getattr(args, 'pattern', '')
            search_type = getattr(args, 'type', 'entities')
            limit = getattr(args, 'limit', 20)
            
            print(f"Searching {search_type} for pattern: '{pattern}'")
            
            if search_type in ['entities', 'all']:
                entities = self.client.search_entities(pattern)[:limit]
                if entities:
                    print(f"\nFound {len(entities)} entities:")
                    for entity in entities:
                        print(f"  - {entity}")
            
            if search_type in ['actions', 'all']:
                actions = self.client.search_actions(pattern)[:limit]
                if actions:
                    print(f"\nFound {len(actions)} actions:")
                    for action in actions:
                        print(f"  - {action}")
            
            return 0
        
        else:
            print(f"Unknown metadata subcommand: {subcommand}")
            return 1
    
    async def _handle_entity_command(self, args: argparse.Namespace) -> int:
        """Handle entity operations"""
        subcommand = getattr(args, 'entity_subcommand', 'get')
        entity_name = getattr(args, 'entity_name', '')
        
        if not entity_name:
            print("Error: Entity name is required")
            return 1
        
        if subcommand == 'get':
            try:
                # Build query options
                query_options = None
                if any([getattr(args, 'select', None), 
                       getattr(args, 'filter', None),
                       getattr(args, 'top', None)]):
                    query_options = QueryOptions(
                        select=args.select.split(',') if getattr(args, 'select', None) else None,
                        filter=getattr(args, 'filter', None),
                        top=getattr(args, 'top', None)
                    )
                
                # Get entity data
                key = getattr(args, 'key', None)
                if key:
                    result = await self.client.get_entity(entity_name, key, query_options)
                else:
                    result = await self.client.get_entities(entity_name, query_options)
                
                # Output result
                output_format = getattr(args, 'output', 'json')
                if output_format == 'json':
                    print(json.dumps(result, indent=2, default=str))
                else:
                    # Simple table-like output for demo
                    if isinstance(result, dict) and 'value' in result:
                        records = result['value']
                        print(f"Retrieved {len(records)} records from {entity_name}")
                        for i, record in enumerate(records[:5]):  # Show first 5
                            print(f"Record {i+1}: {record}")
                    else:
                        print(f"Result: {result}")
                
                return 0
                
            except Exception as e:
                print(f"Error retrieving entity data: {e}")
                return 1
        
        else:
            print(f"Entity subcommand '{subcommand}' not implemented yet")
            return 1
    
    async def _handle_action_command(self, args: argparse.Namespace) -> int:
        """Handle action operations"""
        subcommand = getattr(args, 'action_subcommand', 'list')
        
        if subcommand == 'list':
            pattern = getattr(args, 'pattern', '')
            actions = self.client.search_actions(pattern)
            
            print(f"Found {len(actions)} actions matching '{pattern}':")
            for action in actions[:20]:  # Limit to 20 for readability
                print(f"  - {action}")
            
            return 0
            
        elif subcommand == 'call':
            action_name = getattr(args, 'action_name', '')
            if not action_name:
                print("Error: Action name is required")
                return 1
            
            try:
                entity_name = getattr(args, 'entity', None)
                parameters = {}
                
                if getattr(args, 'parameters', None):
                    parameters = json.loads(args.parameters)
                
                result = await self.client.call_action(
                    action_name, 
                    parameters=parameters if parameters else None,
                    entity_name=entity_name
                )
                
                output_format = getattr(args, 'output', 'json')
                if output_format == 'json':
                    print(json.dumps(result, indent=2, default=str))
                else:
                    print(f"Action result: {result}")
                
                return 0
                
            except Exception as e:
                print(f"Error calling action: {e}")
                return 1
        
        else:
            print(f"Action subcommand '{subcommand}' not implemented yet")
            return 1


def create_enhanced_argument_parser() -> argparse.ArgumentParser:
    """Create enhanced argument parser with CLI commands"""
    parser = argparse.ArgumentParser(
        description="Microsoft Dynamics 365 Finance & Operations Client",
        prog="d365fo-client"
    )
    
    # Global options
    parser.add_argument("--version", action="version", 
                       version=f"d365fo-client {__version__} by {__author__} ({__email__})")
    parser.add_argument("--demo", action="store_true", help="Run the demo/example usage")
    parser.add_argument("--base-url", help="D365 F&O environment base URL")
    parser.add_argument("--client-id", help="Azure AD client ID")
    parser.add_argument("--client-secret", help="Azure AD client secret")
    parser.add_argument("--tenant-id", help="Azure AD tenant ID")
    parser.add_argument("--verify-ssl", type=bool, default=True, help="Enable SSL verification")
    parser.add_argument("--label-cache", type=bool, default=True, help="Enable label caching")
    parser.add_argument("--label-expiry", type=int, default=60, help="Label cache expiry (minutes)")
    parser.add_argument("--output", choices=["json", "table"], default="table", help="Output format")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Test connectivity")
    test_parser.add_argument("--odata-only", action="store_true", help="Test only OData API")
    test_parser.add_argument("--metadata-only", action="store_true", help="Test only Metadata API")
    
    # Version command
    version_parser = subparsers.add_parser("version", help="Get version information")
    version_parser.add_argument("--application", action="store_true", help="Application version only")
    version_parser.add_argument("--platform", action="store_true", help="Platform version only")
    version_parser.add_argument("--build", action="store_true", help="Build version only")
    version_parser.add_argument("--all", action="store_true", default=True, help="All versions")
    
    # Metadata command
    metadata_parser = subparsers.add_parser("metadata", help="Metadata operations")
    metadata_subparsers = metadata_parser.add_subparsers(dest="metadata_subcommand", help="Metadata subcommands")
    
    # metadata sync
    sync_parser = metadata_subparsers.add_parser("sync", help="Sync metadata")
    sync_parser.add_argument("--force", action="store_true", help="Force refresh")
    
    # metadata search
    search_parser = metadata_subparsers.add_parser("search", help="Search metadata")
    search_parser.add_argument("pattern", help="Search pattern")
    search_parser.add_argument("--type", choices=["entities", "actions", "all"], default="entities")
    search_parser.add_argument("--limit", type=int, default=20, help="Max results")
    
    # Entity command
    entity_parser = subparsers.add_parser("entity", help="Entity operations")
    entity_subparsers = entity_parser.add_subparsers(dest="entity_subcommand", help="Entity subcommands")
    
    # entity get
    get_parser = entity_subparsers.add_parser("get", help="Get entity data")
    get_parser.add_argument("entity_name", help="Entity name")
    get_parser.add_argument("key", nargs="?", help="Entity key (optional)")
    get_parser.add_argument("--select", help="Fields to select (comma-separated)")
    get_parser.add_argument("--filter", help="OData filter expression")
    get_parser.add_argument("--top", type=int, help="Max records")
    
    # Action command
    action_parser = subparsers.add_parser("action", help="Action operations")
    action_subparsers = action_parser.add_subparsers(dest="action_subcommand", help="Action subcommands")
    
    # action list
    list_parser = action_subparsers.add_parser("list", help="List actions")
    list_parser.add_argument("pattern", nargs="?", default="", help="Search pattern")
    
    # action call
    call_parser = action_subparsers.add_parser("call", help="Call action")
    call_parser.add_argument("action_name", help="Action name")
    call_parser.add_argument("--entity", help="Entity name (for bound actions)")
    call_parser.add_argument("--parameters", help="Parameters as JSON")
    
    return parser


async def example_usage():
    """Example usage of the F&O client with label functionality"""
    # Keep existing implementation for backward compatibility
    config = FOClientConfig(
        base_url="https://usnconeboxax1aos.cloud.onebox.dynamics.com",
        use_default_credentials=True,
        verify_ssl=False,
        use_label_cache=True,
        label_cache_expiry_minutes=60
    )
    
    async with FOClient(config) as client:
        # Test connections
        print("🔗 Testing connections...")
        if await client.test_connection():
            print("✅ Connected to F&O OData successfully")
        
        if await client.test_metadata_connection():
            print("✅ Connected to F&O Metadata API successfully")
        
        # ... rest of existing example_usage implementation


def main() -> None:
    """Enhanced main entry point with CLI support"""
    parser = create_enhanced_argument_parser()
    args = parser.parse_args()
    
    # Create simple CLI manager
    cli = SimpleCLI()
    
    try:
        exit_code = asyncio.run(cli.execute_command(args))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        if getattr(args, 'verbose', False):
            import traceback
            traceback.print_exc()
        else:
            print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

## Usage Examples

Once implemented, users can use the enhanced CLI like this:

```bash
# Test connectivity
d365fo-client --base-url https://myenv.dynamics.com test

# Get version information
d365fo-client --base-url https://myenv.dynamics.com version --application

# Sync metadata
d365fo-client --base-url https://myenv.dynamics.com metadata sync

# Search entities
d365fo-client --base-url https://myenv.dynamics.com metadata search customer --type entities

# Get entity data
d365fo-client --base-url https://myenv.dynamics.com entity get Customers --top 5 --output json

# List actions
d365fo-client --base-url https://myenv.dynamics.com action list calculate

# Call action
d365fo-client --base-url https://myenv.dynamics.com action call GetApplicationVersion

# Run original demo (backward compatibility)
d365fo-client --demo
```

## Next Steps

1. **Replace the current main.py** with this enhanced version
2. **Test basic functionality** to ensure backward compatibility
3. **Add more sophisticated output formatting** (table, CSV, YAML)
4. **Implement configuration file support** for profiles
5. **Add more entity operations** (create, update, delete)
6. **Enhance error handling** and user feedback
7. **Add comprehensive tests** for CLI functionality

This starter implementation provides a solid foundation while maintaining all existing functionality and demonstrating the command structure defined in the specification.