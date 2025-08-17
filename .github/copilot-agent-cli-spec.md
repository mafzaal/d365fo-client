# GitHub Copilot Agent: d365fo-client CLI Enhancement Specification

## Project Context
The `d365fo-client` is a Python package for interacting with Microsoft Dynamics 365 Finance & Operations environments. We are enhancing the current simple demo utility in `main.py` to become a comprehensive command-line interface (CLI) tool.

## Current State Analysis

### Existing Architecture
- **Main Client**: `FOClient` class with comprehensive async API
- **Configuration**: `FOClientConfig` with Azure AD authentication support
- **Core Features**: Connection testing, metadata operations, CRUD operations, action calls, label operations
- **Current CLI**: Simple `main.py` with `--demo` and `--version` options only

### Available Client Methods
```python
# Connection & Testing
await client.test_connection() -> bool
await client.test_metadata_connection() -> bool

# Version Information  
await client.get_application_version() -> str
await client.get_platform_build_version() -> str
await client.get_application_build_version() -> str

# Metadata Operations
await client.download_metadata(force_refresh=False) -> bool
client.search_entities(pattern: str) -> List[str]
client.search_actions(pattern: str) -> List[str]
await client.get_entity_info_with_labels(entity_name: str) -> EntityInfo

# Entity CRUD Operations
await client.get_entities(entity_name: str, query_options: QueryOptions) -> Dict
await client.get_entity(entity_name: str, key: str, query_options: QueryOptions) -> Dict
await client.create_entity(entity_name: str, data: Dict) -> Dict
await client.update_entity(entity_name: str, key: str, data: Dict) -> Dict
await client.delete_entity(entity_name: str, key: str) -> bool

# Action Operations
await client.call_action(action_name: str, parameters: Dict, entity_name: str) -> Any

# Label Operations
await client.get_label_text(label_id: str, language: str) -> str
await client.get_labels_batch(label_ids: List[str], language: str) -> Dict
```

## CLI Enhancement Requirements

### 1. Command Structure Design
Implement hierarchical command structure using `argparse` subparsers:

```
d365fo-client [GLOBAL_OPTIONS] COMMAND [SUBCOMMAND] [OPTIONS] [ARGUMENTS]
```

### 2. Required Commands

#### Global Options (all commands)
```bash
--base-url URL          # D365 F&O environment URL (required)
--auth-mode MODE        # default|explicit|interactive
--client-id ID          # Azure AD client ID
--client-secret SECRET  # Azure AD client secret  
--tenant-id ID          # Azure AD tenant ID
--verify-ssl BOOL       # SSL verification (default: true)
--output FORMAT         # json|table|csv|yaml (default: table)
--verbose, -v           # Verbose output
--quiet, -q             # Suppress non-essential output
--config FILE           # Configuration file path
--profile NAME          # Configuration profile
```

#### Connection Commands
```bash
# Test connectivity
d365fo-client --base-url <URL> test [--odata-only|--metadata-only]

# Get version information
d365fo-client --base-url <URL> version [--application|--platform|--build|--all]
```

#### Metadata Commands
```bash
# Sync metadata to cache
d365fo-client --base-url <URL> metadata sync [--force]

# Search metadata by pattern
d365fo-client --base-url <URL> metadata search PATTERN [--type entities|actions|all] [--limit N]

# Get entity metadata details
d365fo-client --base-url <URL> metadata info ENTITY_NAME [--properties] [--keys] [--labels]
```

#### Entity Data Commands
```bash
# Get entity data
d365fo-client --base-url <URL> entity get ENTITY_NAME [KEY] [--select fields] [--filter expr] [--top N]

# Create entity record
d365fo-client --base-url <URL> entity create ENTITY_NAME [--data JSON|--file PATH]

# Update entity record  
d365fo-client --base-url <URL> entity update ENTITY_NAME KEY [--data JSON|--file PATH]

# Delete entity record
d365fo-client --base-url <URL> entity delete ENTITY_NAME KEY [--confirm]
```

#### Action Commands
```bash
# List available actions
d365fo-client --base-url <URL> action list [PATTERN] [--entity ENTITY]

# Call OData action
d365fo-client --base-url <URL> action call ACTION_NAME [--entity ENTITY] [--parameters JSON]
```

### 3. Implementation Architecture

#### Core Components to Create
1. **CLI Manager** (`cli.py`): Central command execution orchestrator
2. **Configuration Manager** (`config.py`): Profile-based configuration handling
3. **Output Formatter** (`output.py`): Multi-format output rendering
4. **Enhanced Main** (`main.py`): Argument parsing and entry point

#### Required Dependencies
Add to `pyproject.toml`:
```toml
dependencies = [
    # ... existing dependencies ...
    "tabulate>=0.9.0",     # Table formatting
    "pyyaml>=6.0",         # YAML config files
]
```

## Implementation Guidance for GitHub Copilot

### 1. Argument Parser Structure
When creating the argument parser, use this pattern:

```python
def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Microsoft Dynamics 365 Finance & Operations Client",
        prog="d365fo-client"
    )
    
    # Global options (before subcommands)
    parser.add_argument("--base-url", required=True, help="D365 F&O environment URL")
    # ... other global options
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Add subcommands with their own parsers
    _add_test_command(subparsers)
    _add_version_command(subparsers)
    _add_metadata_commands(subparsers)
    # ... etc
    
    return parser
```

### 2. CLI Manager Pattern
Implement command execution using this pattern:

```python
class CLIManager:
    def __init__(self):
        self.client = None
        self.config_manager = ConfigManager()
        self.output_formatter = None
    
    async def execute_command(self, args: argparse.Namespace) -> int:
        try:
            # Setup
            self.output_formatter = OutputFormatter(args.output)
            config = self._build_config_from_args(args)
            
            # Execute with client
            async with FOClient(config) as client:
                self.client = client
                return await self._route_command(args)
                
        except Exception as e:
            self._handle_error(e, args.verbose)
            return 1
    
    async def _route_command(self, args: argparse.Namespace) -> int:
        handlers = {
            "test": self._handle_test,
            "version": self._handle_version,
            "metadata": self._handle_metadata,
            "entity": self._handle_entity,
            "action": self._handle_action,
        }
        
        handler = handlers.get(args.command)
        if handler:
            return await handler(args)
        else:
            print(f"Unknown command: {args.command}")
            return 1
```

### 3. Output Formatting Pattern
Use this pattern for consistent output formatting:

```python
class OutputFormatter:
    def format_output(self, data: Any, headers: List[str] = None) -> str:
        if self.format_type == "json":
            return json.dumps(data, indent=2, default=str)
        elif self.format_type == "table":
            return self._format_table(data, headers)
        # ... other formats
    
    def _format_table(self, data: Any, headers: List[str] = None) -> str:
        if isinstance(data, list) and data and isinstance(data[0], dict):
            headers = headers or list(data[0].keys())
            rows = [[item.get(h, '') for h in headers] for item in data]
            return tabulate(rows, headers=headers, tablefmt="grid")
        # ... handle other data types
```

### 4. Configuration Management Pattern
Implement profile-based configuration:

```python
@dataclass
class CLIProfile:
    name: str
    base_url: str
    auth_mode: str = "default"
    client_id: Optional[str] = None
    # ... other config fields

class ConfigManager:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self._config_data = self._load_config()
    
    def get_effective_config(self, args: argparse.Namespace) -> FOClientConfig:
        # Merge profile + environment variables + command line args
        # with precedence: args > env vars > profile > defaults
```

### 5. Error Handling Pattern
Implement consistent error handling:

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

### 6. Command Handler Patterns

#### Test Command Handler
```python
async def _handle_test(self, args: argparse.Namespace) -> int:
    success = True
    
    if not args.metadata_only:
        if await self.client.test_connection():
            print("✅ OData API connection successful")
        else:
            print("❌ OData API connection failed")
            success = False
    
    # Similar for metadata connection
    return 0 if success else 1
```

#### Version Command Handler
```python
async def _handle_version(self, args: argparse.Namespace) -> int:
    versions = {}
    
    if args.application or args.all:
        versions['application'] = await self.client.get_application_version()
    
    # Format and output
    output = self.output_formatter.format_output(versions)
    print(output)
    return 0
```

#### Entity Command Handler
```python
async def _handle_entity(self, args: argparse.Namespace) -> int:
    if args.entity_subcommand == "get":
        # Build QueryOptions from args
        query_options = QueryOptions(
            select=args.select.split(',') if args.select else None,
            filter=args.filter,
            top=args.top
        ) if any([args.select, args.filter, args.top]) else None
        
        # Execute query
        if args.key:
            result = await self.client.get_entity(args.entity_name, args.key, query_options)
        else:
            result = await self.client.get_entities(args.entity_name, query_options)
        
        # Format and output
        output = self.output_formatter.format_output(result)
        print(output)
        return 0
```

## Backward Compatibility Requirements

### Maintain Existing Functionality
- Keep existing `--demo` option functional
- Preserve `example_usage()` function for demo mode
- Ensure no breaking changes to existing API

### Legacy Support Pattern
```python
def main() -> None:
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Handle legacy demo mode
    if args.demo or (not args.command and len(sys.argv) == 1):
        print("Running demo mode...")
        try:
            asyncio.run(example_usage())
        except Exception as e:
            print(f"Demo error: {e}")
        return
    
    # New CLI handling
    cli_manager = CLIManager()
    exit_code = asyncio.run(cli_manager.execute_command(args))
    sys.exit(exit_code)
```

## Testing Requirements

### Unit Tests for CLI
```python
# tests/test_cli.py
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
        mock_client_instance = AsyncMock()
        mock_client_instance.get_application_version.return_value = "10.0.12345"
        mock_client.__aenter__.return_value = mock_client_instance
        
        result = await cli.execute_command(args)
        assert result == 0
```

## File Structure After Implementation

```
src/d365fo_client/
├── __init__.py           # Updated exports
├── main.py               # Enhanced with full CLI
├── cli.py                # New: CLI manager
├── config.py             # New: Configuration management
├── output.py             # New: Output formatting
├── client.py             # Existing: No changes needed
├── models.py             # Existing: No changes needed
└── ... (other existing files)
```

## Usage Examples After Implementation

```bash
# Test connectivity
d365fo-client --base-url https://myenv.dynamics.com test

# Get version info as JSON
d365fo-client --base-url https://myenv.dynamics.com version --application --output json

# Sync metadata with force refresh
d365fo-client --base-url https://myenv.dynamics.com metadata sync --force

# Search customer entities
d365fo-client --base-url https://myenv.dynamics.com metadata search customer --type entities

# Get customer data with filtering
d365fo-client --base-url https://myenv.dynamics.com entity get Customers \
  --select "CustomerAccount,Name" --filter "contains(Name,'Contoso')" --top 5 --output table

# Call version action
d365fo-client --base-url https://myenv.dynamics.com action call GetApplicationVersion

# Run original demo (backward compatibility)
d365fo-client --demo
```

## Key Success Criteria

1. **Backward Compatibility**: Existing `--demo` functionality preserved
2. **Comprehensive CLI**: All major client features exposed via command line
3. **Flexible Configuration**: Environment-based URL support with profiles
4. **Multi-Format Output**: JSON, table, CSV, YAML output options
5. **Error Handling**: Clear, actionable error messages
6. **Performance**: Efficient execution with proper async handling
7. **Testing**: Comprehensive test coverage for CLI functionality

## Implementation Priority

### Phase 1 (MVP)
1. Enhanced argument parser with subcommands
2. Basic CLI manager with command routing
3. Test and version commands
4. Simple output formatting (JSON + basic table)

### Phase 2 (Core Features)
1. Metadata sync and search commands
2. Basic entity get operations
3. Action list and call commands
4. Enhanced error handling

### Phase 3 (Advanced Features)
1. Complete entity CRUD operations
2. Configuration file support
3. Advanced output formatting
4. Comprehensive testing

This specification provides GitHub Copilot with comprehensive context to assist in implementing a robust, feature-complete CLI for the d365fo-client package while maintaining backward compatibility and following best practices.