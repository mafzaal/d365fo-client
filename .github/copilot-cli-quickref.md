# GitHub Copilot Quick Reference: d365fo-client CLI Implementation

## Context Summary
Enhancing `d365fo-client` from a simple demo utility to a comprehensive CLI tool for D365 Finance & Operations operations.

## Key Implementation Patterns

### 1. Argument Parser Structure
```python
def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Microsoft Dynamics 365 Finance & Operations Client",
        prog="d365fo-client"
    )
    
    # Global options (required before subcommands)
    parser.add_argument("--base-url", help="D365 F&O environment URL")
    parser.add_argument("--output", choices=["json", "table", "csv", "yaml"], 
                       default="table", help="Output format")
    parser.add_argument("--verbose", "-v", action="store_true")
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    return parser
```

### 2. CLI Manager Pattern
```python
class CLIManager:
    async def execute_command(self, args: argparse.Namespace) -> int:
        try:
            # Create client with config from args
            config = self._build_config_from_args(args)
            async with FOClient(config) as client:
                self.client = client
                return await self._route_command(args)
        except Exception as e:
            self._handle_error(e, args.verbose)
            return 1
```

### 3. Command Handler Pattern
```python
async def _handle_test(self, args: argparse.Namespace) -> int:
    """Test connectivity command"""
    success = True
    
    if not getattr(args, 'metadata_only', False):
        if await self.client.test_connection():
            print("✅ OData API connection successful")
        else:
            print("❌ OData API connection failed")
            success = False
    
    return 0 if success else 1
```

### 4. Output Formatting Pattern
```python
class OutputFormatter:
    def format_output(self, data: Any) -> str:
        if self.format_type == "json":
            return json.dumps(data, indent=2, default=str)
        elif self.format_type == "table":
            return self._format_table(data)
        # ... other formats
```

## Required Commands Implementation

### Test Command
```python
# Add to subparsers
test_parser = subparsers.add_parser("test", help="Test connectivity")
test_parser.add_argument("--odata-only", action="store_true")
test_parser.add_argument("--metadata-only", action="store_true")

# Handler uses: await client.test_connection(), await client.test_metadata_connection()
```

### Version Command
```python
# Add to subparsers
version_parser = subparsers.add_parser("version", help="Get version information")
version_parser.add_argument("--application", action="store_true")
version_parser.add_argument("--platform", action="store_true")
version_parser.add_argument("--build", action="store_true")

# Handler uses: await client.get_application_version(), etc.
```

### Metadata Commands
```python
# Add to subparsers
metadata_parser = subparsers.add_parser("metadata", help="Metadata operations")
metadata_subs = metadata_parser.add_subparsers(dest="metadata_subcommand")

# sync subcommand
sync_parser = metadata_subs.add_parser("sync", help="Sync metadata")
sync_parser.add_argument("--force", action="store_true")

# search subcommand  
search_parser = metadata_subs.add_parser("search", help="Search metadata")
search_parser.add_argument("pattern", help="Search pattern")
search_parser.add_argument("--type", choices=["entities", "actions", "all"], default="entities")

# Handler uses: await client.download_metadata(), client.search_entities(), client.search_actions()
```

### Entity Commands
```python
# Add to subparsers
entity_parser = subparsers.add_parser("entity", help="Entity operations")
entity_subs = entity_parser.add_subparsers(dest="entity_subcommand")

# get subcommand
get_parser = entity_subs.add_parser("get", help="Get entity data")
get_parser.add_argument("entity_name", help="Entity name")
get_parser.add_argument("key", nargs="?", help="Entity key (optional)")
get_parser.add_argument("--select", help="Fields to select")
get_parser.add_argument("--filter", help="OData filter")
get_parser.add_argument("--top", type=int, help="Max records")

# Handler uses: await client.get_entities(), await client.get_entity()
# Build QueryOptions from args: QueryOptions(select=args.select.split(','), filter=args.filter, top=args.top)
```

### Action Commands
```python
# Add to subparsers
action_parser = subparsers.add_parser("action", help="Action operations")
action_subs = action_parser.add_subparsers(dest="action_subcommand")

# list subcommand
list_parser = action_subs.add_parser("list", help="List actions")
list_parser.add_argument("pattern", nargs="?", default="", help="Search pattern")

# call subcommand
call_parser = action_subs.add_parser("call", help="Call action")
call_parser.add_argument("action_name", help="Action name")
call_parser.add_argument("--entity", help="Entity name")
call_parser.add_argument("--parameters", help="Parameters as JSON")

# Handler uses: client.search_actions(), await client.call_action()
```

## Available Client Methods Reference

### Connection & Testing
- `await client.test_connection() -> bool`
- `await client.test_metadata_connection() -> bool`

### Version Information
- `await client.get_application_version() -> str`
- `await client.get_platform_build_version() -> str`
- `await client.get_application_build_version() -> str`

### Metadata Operations
- `await client.download_metadata(force_refresh=False) -> bool`
- `client.search_entities(pattern: str) -> List[str]`
- `client.search_actions(pattern: str) -> List[str]`
- `await client.get_entity_info_with_labels(entity_name: str) -> EntityInfo`

### Entity Operations
- `await client.get_entities(entity_name: str, query_options: QueryOptions) -> Dict`
- `await client.get_entity(entity_name: str, key: str, query_options: QueryOptions) -> Dict`
- `await client.create_entity(entity_name: str, data: Dict) -> Dict`
- `await client.update_entity(entity_name: str, key: str, data: Dict) -> Dict`
- `await client.delete_entity(entity_name: str, key: str) -> bool`

### Action Operations
- `await client.call_action(action_name: str, parameters: Dict, entity_name: str) -> Any`

## Configuration Pattern
```python
# Build FOClientConfig from args
config = FOClientConfig(
    base_url=args.base_url,
    use_default_credentials=not any([args.client_id, args.client_secret]),
    client_id=args.client_id,
    client_secret=args.client_secret,
    tenant_id=args.tenant_id,
    verify_ssl=getattr(args, 'verify_ssl', True),
    use_label_cache=getattr(args, 'label_cache', True)
)
```

## Error Handling Pattern
```python
def _handle_error(self, error: Exception, verbose: bool = False) -> None:
    if isinstance(error, FOClientError):
        print(f"Error: {error}")
    else:
        if verbose:
            import traceback
            traceback.print_exc()
        else:
            print(f"Unexpected error: {error}")
```

## Backward Compatibility
```python
def main() -> None:
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Handle legacy demo mode
    if args.demo or (not hasattr(args, 'command') or not args.command):
        print("Running demo mode...")
        try:
            asyncio.run(example_usage())
            return
        except Exception as e:
            print(f"Demo error: {e}")
            return
    
    # New CLI handling
    cli_manager = CLIManager()
    exit_code = asyncio.run(cli_manager.execute_command(args))
    sys.exit(exit_code)
```

## File Structure to Create
```
src/d365fo_client/
├── main.py          # Enhanced with full CLI
├── cli.py           # New: CLI manager
├── config.py        # New: Configuration management  
├── output.py        # New: Output formatting
└── ... (existing files unchanged)
```

## Required Dependencies
Add to `pyproject.toml`:
```toml
dependencies = [
    # ... existing ...
    "tabulate>=0.9.0",     # Table formatting
    "pyyaml>=6.0",         # YAML config files
]
```

## Testing Pattern
```python
@pytest.mark.asyncio
async def test_version_command():
    cli = CLIManager()
    args = argparse.Namespace(
        command="version",
        application=True,
        base_url="https://test.dynamics.com",
        output="json"
    )
    
    with patch('d365fo_client.cli.FOClient') as mock_client:
        # Mock client setup
        result = await cli.execute_command(args)
        assert result == 0
```

## Success Criteria
1. ✅ Backward compatibility (`--demo` works)
2. ✅ All major client features exposed via CLI
3. ✅ Environment base URL support
4. ✅ Multiple output formats
5. ✅ Comprehensive error handling
6. ✅ Async execution with proper error codes