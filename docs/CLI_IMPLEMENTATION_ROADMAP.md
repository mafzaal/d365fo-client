# CLI Implementation Roadmap for d365fo-client

## Overview
This document provides a detailed implementation roadmap for transforming the current `main.py` demo utility into a comprehensive command-line interface based on the CLI specification.

## Current Architecture Analysis

### Existing Components
The current implementation has these key components that can be leveraged:

1. **FOClient**: Main client with comprehensive async API
2. **Configuration**: FOClientConfig with environment support
3. **Authentication**: AuthenticationManager with Azure AD integration
4. **Metadata**: MetadataManager with caching and search
5. **CRUD Operations**: Full entity CRUD support
6. **Action Operations**: OData action calling capability
7. **Label Operations**: Label retrieval and caching
8. **Query Builder**: Advanced OData query support

### Current main.py Structure
- Simple argument parser with `--demo` and `--version` options
- Single `example_usage()` async function demonstrating all features
- Minimal error handling and output formatting

## Implementation Strategy

### Phase 1: CLI Framework Foundation

#### 1.1 Enhanced Argument Parsing
Create a hierarchical command structure using `argparse` subparsers:

```python
# Enhanced main.py structure
import argparse
import asyncio
import sys
from typing import Optional, Dict, Any

from .cli import CLIManager
from .config import ConfigManager
from .output import OutputFormatter

def create_argument_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands"""
    parser = argparse.ArgumentParser(
        description="Microsoft Dynamics 365 Finance & Operations Client",
        prog="d365fo-client"
    )
    
    # Global options
    parser.add_argument("--base-url", help="D365 F&O environment base URL")
    parser.add_argument("--auth-mode", choices=["default", "explicit", "interactive"], 
                       default="default", help="Authentication mode")
    parser.add_argument("--client-id", help="Azure AD client ID")
    parser.add_argument("--client-secret", help="Azure AD client secret") 
    parser.add_argument("--tenant-id", help="Azure AD tenant ID")
    parser.add_argument("--verify-ssl", type=bool, default=True, help="Enable SSL verification")
    parser.add_argument("--cache-dir", help="Metadata cache directory")
    parser.add_argument("--label-cache", type=bool, default=True, help="Enable label caching")
    parser.add_argument("--label-expiry", type=int, default=60, help="Label cache expiry (minutes)")
    parser.add_argument("--language", default="en-US", help="Language code for labels")
    parser.add_argument("--output", choices=["json", "table", "csv", "yaml"], 
                       default="table", help="Output format")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress non-essential output")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--profile", help="Configuration profile to use")
    
    # Legacy option for backward compatibility
    parser.add_argument("--demo", action="store_true", help="Run the demo/example usage")
    parser.add_argument("--version", action="version", 
                       version=f"d365fo-client {__version__} by {__author__} ({__email__})")
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Connection commands
    _add_test_command(subparsers)
    _add_version_command(subparsers)
    
    # Metadata commands
    _add_metadata_commands(subparsers)
    
    # Entity commands
    _add_entity_commands(subparsers)
    
    # Action commands
    _add_action_commands(subparsers)
    
    # Label commands
    _add_label_commands(subparsers)
    
    # Configuration commands
    _add_config_commands(subparsers)
    
    return parser
```

#### 1.2 Configuration Management System
Create a new `config.py` module for profile-based configuration:

```python
# src/d365fo_client/config.py
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class CLIProfile:
    """CLI configuration profile"""
    name: str
    base_url: str
    auth_mode: str = "default"
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    tenant_id: Optional[str] = None
    verify_ssl: bool = True
    cache_dir: Optional[str] = None
    label_cache: bool = True
    label_expiry: int = 60
    language: str = "en-US"
    output_format: str = "table"

class ConfigManager:
    """Manages CLI configuration profiles"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config_dir = Path(self.config_path).parent
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._config_data = self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path"""
        home = Path.home()
        return str(home / ".d365fo-client" / "config.yaml")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if not Path(self.config_path).exists():
            return {"profiles": {}, "default_profile": None}
        
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f) or {"profiles": {}, "default_profile": None}
    
    def save_config(self):
        """Save configuration to file"""
        with open(self.config_path, 'w') as f:
            yaml.dump(self._config_data, f, default_flow_style=False)
    
    def create_profile(self, profile: CLIProfile):
        """Create or update a profile"""
        self._config_data["profiles"][profile.name] = asdict(profile)
        self.save_config()
    
    def get_profile(self, name: str) -> Optional[CLIProfile]:
        """Get a profile by name"""
        profile_data = self._config_data["profiles"].get(name)
        if profile_data:
            return CLIProfile(**profile_data)
        return None
    
    def list_profiles(self) -> List[str]:
        """List all profile names"""
        return list(self._config_data["profiles"].keys())
    
    def delete_profile(self, name: str) -> bool:
        """Delete a profile"""
        if name in self._config_data["profiles"]:
            del self._config_data["profiles"][name]
            if self._config_data.get("default_profile") == name:
                self._config_data["default_profile"] = None
            self.save_config()
            return True
        return False
    
    def set_default_profile(self, name: str):
        """Set default profile"""
        if name in self._config_data["profiles"]:
            self._config_data["default_profile"] = name
            self.save_config()
    
    def get_effective_config(self, args: argparse.Namespace) -> FOClientConfig:
        """Get effective configuration from args and profiles"""
        # Start with profile if specified
        profile = None
        if args.profile:
            profile = self.get_profile(args.profile)
        elif self._config_data.get("default_profile"):
            profile = self.get_profile(self._config_data["default_profile"])
        
        # Build config with precedence: args > profile > defaults
        config_dict = {}
        
        if profile:
            config_dict.update(asdict(profile))
        
        # Override with command line arguments
        for key, value in vars(args).items():
            if value is not None and key != 'command':
                # Map CLI args to config keys
                config_key = self._map_cli_arg_to_config(key)
                if config_key:
                    config_dict[config_key] = value
        
        return FOClientConfig(**config_dict)
```

#### 1.3 Output Formatting System
Create a new `output.py` module for flexible output formatting:

```python
# src/d365fo_client/output.py
import json
import csv
import yaml
from typing import Any, Dict, List, Union
from io import StringIO
from tabulate import tabulate

class OutputFormatter:
    """Handles output formatting for different formats"""
    
    def __init__(self, format_type: str = "table"):
        self.format_type = format_type.lower()
    
    def format_output(self, data: Any, headers: List[str] = None) -> str:
        """Format data according to the specified format"""
        if self.format_type == "json":
            return self._format_json(data)
        elif self.format_type == "table":
            return self._format_table(data, headers)
        elif self.format_type == "csv":
            return self._format_csv(data, headers)
        elif self.format_type == "yaml":
            return self._format_yaml(data)
        else:
            raise ValueError(f"Unsupported format: {self.format_type}")
    
    def _format_json(self, data: Any) -> str:
        """Format as JSON"""
        return json.dumps(data, indent=2, default=str)
    
    def _format_table(self, data: Any, headers: List[str] = None) -> str:
        """Format as table using tabulate"""
        if isinstance(data, list) and data:
            if isinstance(data[0], dict):
                headers = headers or list(data[0].keys())
                rows = [[item.get(h, '') for h in headers] for item in data]
                return tabulate(rows, headers=headers, tablefmt="grid")
            else:
                return tabulate([[item] for item in data], headers=headers or ["Value"], tablefmt="grid")
        elif isinstance(data, dict):
            rows = [[k, v] for k, v in data.items()]
            return tabulate(rows, headers=["Key", "Value"], tablefmt="grid")
        else:
            return str(data)
    
    def _format_csv(self, data: Any, headers: List[str] = None) -> str:
        """Format as CSV"""
        output = StringIO()
        if isinstance(data, list) and data:
            if isinstance(data[0], dict):
                headers = headers or list(data[0].keys())
                writer = csv.DictWriter(output, fieldnames=headers)
                writer.writeheader()
                writer.writerows(data)
            else:
                writer = csv.writer(output)
                if headers:
                    writer.writerow(headers)
                for item in data:
                    writer.writerow([item])
        return output.getvalue()
    
    def _format_yaml(self, data: Any) -> str:
        """Format as YAML"""
        return yaml.dump(data, default_flow_style=False, default=str)
```

### Phase 2: Command Implementation

#### 2.1 CLI Manager Class
Create a central CLI manager to handle command execution:

```python
# src/d365fo_client/cli.py
import asyncio
import sys
from typing import Dict, Any, Optional, Callable
from .client import FOClient
from .config import ConfigManager
from .output import OutputFormatter
from .exceptions import FOClientError

class CLIManager:
    """Main CLI command manager"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.output_formatter = None
        self.client = None
    
    async def execute_command(self, args: argparse.Namespace) -> int:
        """Execute the specified command"""
        try:
            # Setup output formatter
            self.output_formatter = OutputFormatter(args.output)
            
            # Handle legacy demo mode
            if args.demo or (not args.command and len(sys.argv) == 1):
                return await self._run_demo()
            
            # Handle configuration commands (no client needed)
            if args.command == "config":
                return await self._handle_config_commands(args)
            
            # Get effective configuration
            config = self.config_manager.get_effective_config(args)
            
            # Validate required configuration
            if not config.base_url:
                print("Error: Base URL is required. Use --base-url or configure a profile.")
                return 1
            
            # Create and initialize client
            async with FOClient(config) as client:
                self.client = client
                
                # Route to appropriate command handler
                command_handlers = {
                    "test": self._handle_test_command,
                    "version": self._handle_version_command,
                    "metadata": self._handle_metadata_commands,
                    "entity": self._handle_entity_commands,
                    "action": self._handle_action_commands,
                    "label": self._handle_label_commands,
                }
                
                handler = command_handlers.get(args.command)
                if handler:
                    return await handler(args)
                else:
                    print(f"Unknown command: {args.command}")
                    return 1
                    
        except FOClientError as e:
            print(f"Error: {e}")
            return 1
        except Exception as e:
            if args.verbose:
                import traceback
                traceback.print_exc()
            else:
                print(f"Unexpected error: {e}")
            return 1
    
    async def _handle_test_command(self, args: argparse.Namespace) -> int:
        """Handle test connectivity command"""
        if not args.quiet:
            print("Testing connectivity to D365 F&O environment...")
        
        success = True
        
        if not args.metadata_only:
            if await self.client.test_connection():
                if not args.quiet:
                    print("✅ OData API connection successful")
            else:
                print("❌ OData API connection failed")
                success = False
        
        if not args.odata_only:
            if await self.client.test_metadata_connection():
                if not args.quiet:
                    print("✅ Metadata API connection successful")
            else:
                print("❌ Metadata API connection failed")
                success = False
        
        return 0 if success else 1
    
    async def _handle_version_command(self, args: argparse.Namespace) -> int:
        """Handle version information command"""
        version_info = {}
        
        try:
            if args.all or args.application:
                version_info["application"] = await self.client.get_application_version()
            
            if args.all or args.platform:
                version_info["platform_build"] = await self.client.get_platform_build_version()
                
            if args.all or args.build:
                version_info["application_build"] = await self.client.get_application_build_version()
                
            if not version_info:
                # Default to all if no specific version requested
                version_info = {
                    "application": await self.client.get_application_version(),
                    "platform_build": await self.client.get_platform_build_version(),
                    "application_build": await self.client.get_application_build_version()
                }
            
            output = self.output_formatter.format_output(version_info)
            print(output)
            return 0
            
        except Exception as e:
            print(f"Error retrieving version information: {e}")
            return 1
```

#### 2.2 Metadata Commands Implementation
```python
async def _handle_metadata_commands(self, args: argparse.Namespace) -> int:
    """Handle metadata subcommands"""
    if args.metadata_command == "sync":
        return await self._metadata_sync(args)
    elif args.metadata_command == "search":
        return await self._metadata_search(args)
    elif args.metadata_command == "info":
        return await self._metadata_info(args)
    else:
        print(f"Unknown metadata command: {args.metadata_command}")
        return 1

async def _metadata_sync(self, args: argparse.Namespace) -> int:
    """Sync metadata to local cache"""
    if not args.quiet:
        print("Syncing metadata...")
    
    success = await self.client.download_metadata(force_refresh=args.force)
    
    if success:
        if not args.quiet:
            print("✅ Metadata sync completed successfully")
        return 0
    else:
        print("❌ Metadata sync failed")
        return 1

async def _metadata_search(self, args: argparse.Namespace) -> int:
    """Search metadata by pattern"""
    results = []
    
    if args.type in ["entities", "all"]:
        entities = self.client.search_entities(args.pattern)
        for entity in entities[:args.limit]:
            results.append({
                "type": "entity",
                "name": entity,
                "category": "N/A"  # Could be enhanced with category info
            })
    
    if args.type in ["actions", "all"]:
        actions = self.client.search_actions(args.pattern)
        for action in actions[:args.limit]:
            results.append({
                "type": "action", 
                "name": action,
                "category": "N/A"
            })
    
    # Apply limit to total results
    results = results[:args.limit]
    
    if results:
        output = self.output_formatter.format_output(results)
        print(output)
        return 0
    else:
        if not args.quiet:
            print(f"No {args.type} found matching '{args.pattern}'")
        return 0

async def _metadata_info(self, args: argparse.Namespace) -> int:
    """Get detailed metadata information for an entity"""
    try:
        entity_info = await self.client.get_entity_info_with_labels(
            args.entity_name, resolve_labels=args.labels
        )
        
        if entity_info:
            info_dict = {
                "name": entity_info.name,
                "label": entity_info.label_text or entity_info.label_id,
                "property_count": len(entity_info.enhanced_properties)
            }
            
            if args.properties:
                properties = []
                for prop in entity_info.enhanced_properties:
                    prop_info = {
                        "name": prop.name,
                        "type": prop.type,
                        "is_key": prop.is_key,
                        "is_nullable": prop.nullable
                    }
                    if args.labels and prop.label_text:
                        prop_info["label"] = prop.label_text
                    properties.append(prop_info)
                
                if args.keys:
                    properties = [p for p in properties if p["is_key"]]
                
                info_dict["properties"] = properties
            
            output = self.output_formatter.format_output(info_dict)
            print(output)
            return 0
        else:
            print(f"Entity '{args.entity_name}' not found")
            return 1
            
    except Exception as e:
        print(f"Error retrieving entity information: {e}")
        return 1
```

#### 2.3 Entity Commands Implementation
```python
async def _handle_entity_commands(self, args: argparse.Namespace) -> int:
    """Handle entity subcommands"""
    if args.entity_command == "get":
        return await self._entity_get(args)
    elif args.entity_command == "create":
        return await self._entity_create(args)
    elif args.entity_command == "update":
        return await self._entity_update(args)
    elif args.entity_command == "delete":
        return await self._entity_delete(args)
    else:
        print(f"Unknown entity command: {args.entity_command}")
        return 1

async def _entity_get(self, args: argparse.Namespace) -> int:
    """Get entity data"""
    try:
        # Build query options
        query_options = None
        if any([args.select, args.filter, args.orderby, args.top, args.skip, args.expand]):
            query_options = QueryOptions(
                select=args.select.split(',') if args.select else None,
                filter=args.filter,
                orderby=args.orderby.split(',') if args.orderby else None,
                top=args.top,
                skip=args.skip,
                expand=args.expand.split(',') if args.expand else None,
                count=args.count
            )
        
        # Get data
        if args.key:
            # Get single entity by key
            result = await self.client.get_entity(args.entity_name, args.key, query_options)
        else:
            # Get entity collection
            result = await self.client.get_entities(args.entity_name, query_options)
        
        # Format and output result
        output = self.output_formatter.format_output(result)
        print(output)
        return 0
        
    except Exception as e:
        print(f"Error retrieving entity data: {e}")
        return 1

async def _entity_create(self, args: argparse.Namespace) -> int:
    """Create new entity record"""
    try:
        # Get data from args or file
        if args.file:
            with open(args.file, 'r') as f:
                data = json.load(f)
        elif args.data:
            data = json.loads(args.data)
        else:
            print("Error: Either --data or --file must be specified")
            return 1
        
        # Create entity
        result = await self.client.create_entity(args.entity_name, data)
        
        if not args.quiet:
            print("✅ Entity created successfully")
        
        if args.verbose:
            output = self.output_formatter.format_output(result)
            print(output)
        
        return 0
        
    except Exception as e:
        print(f"Error creating entity: {e}")
        return 1
```

### Phase 3: Advanced Features

#### 3.1 Subcommand Definitions
Add comprehensive subcommand definitions:

```python
def _add_metadata_commands(subparsers):
    """Add metadata commands"""
    metadata_parser = subparsers.add_parser("metadata", help="Metadata operations")
    metadata_subparsers = metadata_parser.add_subparsers(dest="metadata_command")
    
    # metadata sync
    sync_parser = metadata_subparsers.add_parser("sync", help="Download and cache metadata")
    sync_parser.add_argument("--force", action="store_true", help="Force refresh of metadata cache")
    sync_parser.add_argument("--entities-only", action="store_true", help="Download only entity metadata")
    sync_parser.add_argument("--actions-only", action="store_true", help="Download only action metadata")
    
    # metadata search  
    search_parser = metadata_subparsers.add_parser("search", help="Search metadata by pattern")
    search_parser.add_argument("pattern", help="Search pattern")
    search_parser.add_argument("--type", choices=["entities", "actions", "enums", "all"], 
                              default="all", help="Metadata type to search")
    search_parser.add_argument("--category", help="Entity category filter")
    search_parser.add_argument("--limit", type=int, default=50, help="Maximum results")
    search_parser.add_argument("--details", action="store_true", help="Show detailed information")
    
    # metadata info
    info_parser = metadata_subparsers.add_parser("info", help="Get detailed metadata information")
    info_parser.add_argument("entity_name", help="Entity name")
    info_parser.add_argument("--properties", action="store_true", help="Show entity properties")
    info_parser.add_argument("--keys", action="store_true", help="Show key properties only")
    info_parser.add_argument("--navigation", action="store_true", help="Show navigation properties")
    info_parser.add_argument("--labels", action="store_true", help="Resolve and show labels")

def _add_entity_commands(subparsers):
    """Add entity commands"""
    entity_parser = subparsers.add_parser("entity", help="Entity operations")
    entity_subparsers = entity_parser.add_subparsers(dest="entity_command")
    
    # entity get
    get_parser = entity_subparsers.add_parser("get", help="Retrieve data from entity")
    get_parser.add_argument("entity_name", help="Entity name")
    get_parser.add_argument("key", nargs="?", help="Entity key (optional)")
    get_parser.add_argument("--select", help="Comma-separated fields to select")
    get_parser.add_argument("--filter", help="OData filter expression")
    get_parser.add_argument("--orderby", help="Comma-separated fields to order by")
    get_parser.add_argument("--top", type=int, help="Maximum records to return")
    get_parser.add_argument("--skip", type=int, help="Number of records to skip")
    get_parser.add_argument("--expand", help="Navigation properties to expand")
    get_parser.add_argument("--count", action="store_true", help="Include total count")
    
    # entity create
    create_parser = entity_subparsers.add_parser("create", help="Create new entity record")
    create_parser.add_argument("entity_name", help="Entity name")
    create_parser.add_argument("--data", help="JSON data for the new record")
    create_parser.add_argument("--file", help="JSON file containing record data")
    
    # entity update
    update_parser = entity_subparsers.add_parser("update", help="Update existing entity record")
    update_parser.add_argument("entity_name", help="Entity name")
    update_parser.add_argument("key", help="Entity key")
    update_parser.add_argument("--data", help="JSON data for updates")
    update_parser.add_argument("--file", help="JSON file containing update data")
    update_parser.add_argument("--patch", action="store_true", help="Use PATCH method")
    
    # entity delete
    delete_parser = entity_subparsers.add_parser("delete", help="Delete entity record")
    delete_parser.add_argument("entity_name", help="Entity name")
    delete_parser.add_argument("key", help="Entity key")
    delete_parser.add_argument("--confirm", action="store_true", help="Skip confirmation prompt")
```

### Phase 4: Integration and Testing

#### 4.1 Enhanced main.py Structure
```python
# Updated main.py
"""Enhanced main module for d365fo-client package with comprehensive CLI."""

import asyncio
import argparse
import sys
from typing import Optional

from .cli import CLIManager
from .config import ConfigManager
from .output import OutputFormatter
from . import __version__, __author__, __email__

def create_argument_parser() -> argparse.ArgumentParser:
    """Create the comprehensive argument parser"""
    # Implementation as shown above
    pass

def main() -> None:
    """Enhanced main entry point with full CLI support"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Create CLI manager and execute command
    cli_manager = CLIManager()
    
    try:
        exit_code = asyncio.run(cli_manager.execute_command(args))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        if args.verbose if hasattr(args, 'verbose') else False:
            import traceback
            traceback.print_exc()
        else:
            print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

#### 4.2 Dependencies Addition
Add required dependencies to `pyproject.toml`:

```toml
dependencies = [
    # ... existing dependencies ...
    "tabulate>=0.9.0",     # For table formatting
    "pyyaml>=6.0",         # For YAML configuration files
    "click>=8.0.0",        # Alternative: more advanced CLI framework
]
```

#### 4.3 Testing Strategy
Create comprehensive tests for the CLI:

```python
# tests/test_cli.py
import pytest
import tempfile
import json
from unittest.mock import AsyncMock, patch

from d365fo_client.cli import CLIManager
from d365fo_client.config import ConfigManager, CLIProfile

class TestCLI:
    """Test CLI functionality"""
    
    @pytest.fixture
    def temp_config(self):
        """Create temporary configuration"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_path = f.name
        
        config_manager = ConfigManager(config_path)
        yield config_manager
        
        # Cleanup
        os.unlink(config_path)
    
    @pytest.mark.asyncio
    async def test_version_command(self, temp_config):
        """Test version command execution"""
        cli_manager = CLIManager()
        cli_manager.config_manager = temp_config
        
        with patch('d365fo_client.cli.FOClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get_application_version.return_value = "10.0.12345"
            mock_client.__aenter__.return_value = mock_client_instance
            
            args = argparse.Namespace(
                base_url="https://test.dynamics.com",
                command="version",
                application=True,
                output="json",
                verbose=False,
                quiet=False
            )
            
            result = await cli_manager.execute_command(args)
            assert result == 0
            mock_client_instance.get_application_version.assert_called_once()
```

## Implementation Timeline

### Week 1-2: Foundation
- [ ] Enhanced argument parsing structure
- [ ] Configuration management system
- [ ] Output formatting system
- [ ] Basic CLI manager framework

### Week 3-4: Core Commands
- [ ] Test and version commands
- [ ] Basic metadata sync and search
- [ ] Simple entity get operations
- [ ] Error handling and logging

### Week 5-6: Advanced Features
- [ ] Complete entity CRUD operations
- [ ] Action operations
- [ ] Label operations
- [ ] Advanced metadata commands

### Week 7-8: Polish and Testing
- [ ] Comprehensive test suite
- [ ] Documentation updates
- [ ] Performance optimization
- [ ] Configuration file examples

## Considerations

### Backward Compatibility
- Keep existing `--demo` option functional
- Preserve existing `example_usage()` function
- Maintain current API structure

### Performance
- Implement connection pooling for multiple operations
- Add caching for frequently accessed metadata
- Support parallel execution where appropriate

### Security
- Secure credential storage in configuration files
- Environment variable substitution
- Profile-based isolation

### User Experience
- Progressive disclosure (simple commands first)
- Helpful error messages with suggestions
- Consistent output formatting
- Interactive confirmation for destructive operations

This roadmap provides a comprehensive path to transform the current simple demo utility into a powerful, production-ready command-line interface for D365 Finance & Operations.