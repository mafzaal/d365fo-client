# Dynamics 365 Finance & Operations Client and MCP Server

A comprehensive Python client library for Microsoft Dynamics 365 Finance & Operations (D365 F&O) that provides easy access to OData endpoints, metadata operations, and label management.

## Features

- 🔗 **OData Client**: Full CRUD operations on D365 F&O data entities
- 📊 **Metadata Management**: Download, cache, and search entity/action metadata  
- 🏷️ **Label Operations**: Retrieve and cache multilingual labels with advanced search
- 🔍 **Advanced Querying**: Support for all OData query parameters ($select, $filter, $expand, etc.)
- ⚡ **Action Execution**: Execute both bound and unbound OData actions
- 🔒 **Authentication**: Support for Azure AD authentication (default credentials or client secrets)
- 💾 **Intelligent Caching**: Built-in caching for metadata and labels to improve performance
- 🌐 **Async/Await**: Modern async/await pattern for optimal performance
- 📝 **Type Hints**: Full type annotation support for better IDE experience
- 🤖 **MCP Server**: Model Context Protocol server for AI assistant integration with 12 tools and 4 resource types

## Installation

```bash
# Install from PyPI (when published)
pip install d365fo-client

# Or install from source
git clone https://github.com/mafzaal/d365fo-client.git
cd d365fo-client
pip install -e .
```

**Note**: The package includes MCP (Model Context Protocol) dependencies by default, enabling AI assistant integration. The `d365fo-mcp-server` command will be available after installation.

## Quick Start

## Command Line Interface (CLI)

d365fo-client provides a CLI for interacting with Dynamics 365 Finance & Operations APIs and metadata. The CLI allows you to perform common operations directly from your terminal.

### Usage

```sh
python -m d365fo_client.cli [OPTIONS] COMMAND [ARGS]
```

### Example Commands

- `get-version` — Retrieve the application version.
- `list-entities` — List available metadata entities.
- `cache-metadata` — Cache metadata locally for faster access.
- `help` — Show available commands and options.

### Options

- `--config PATH` — Specify a custom configuration file.
- `--verbose` — Enable verbose output for debugging.

For a full list of commands and options, run:

```sh
python -m d365fo_client.cli --help
```
### Basic Usage

```python
import asyncio
from d365fo_client import FOClient, FOClientConfig

async def main():
    # Simple configuration
    config = FOClientConfig(
        base_url="https://your-fo-environment.dynamics.com",
        use_default_credentials=True  # Uses Azure Default Credential
    )
    
    async with FOClient(config) as client:
        # Test connection
        if await client.test_connection():
            print("✅ Connected successfully!")
        
        # Download metadata
        await client.download_metadata()
        
        # Search for entities
        customer_entities = client.search_entities("customer")
        print(f"Found {len(customer_entities)} customer entities")
        
        # Get customers with query options
        from d365fo_client import QueryOptions
        options = QueryOptions(
            select=["CustomerAccount", "Name", "SalesCurrencyCode"],
            top=10,
            orderby=["Name"]
        )
        
        customers = await client.get_entities("Customers", options)
        print(f"Retrieved {len(customers['value'])} customers")

if __name__ == "__main__":
    asyncio.run(main())
```

### Using Convenience Function

```python
from d365fo_client import create_client

# Quick client creation
async with create_client("https://your-fo-environment.dynamics.com") as client:
    customers = await client.get_entities("Customers", top=5)
```

## Configuration

### Authentication Options

```python
from d365fo_client import FOClientConfig

# Option 1: Default Azure credentials (recommended)
config = FOClientConfig(
    base_url="https://your-fo-environment.dynamics.com",
    use_default_credentials=True
)

# Option 2: Client credentials
config = FOClientConfig(
    base_url="https://your-fo-environment.dynamics.com",
    client_id="your-client-id",
    client_secret="your-client-secret", 
    tenant_id="your-tenant-id",
    use_default_credentials=False
)

# Option 3: With custom settings
config = FOClientConfig(
    base_url="https://your-fo-environment.dynamics.com",
    use_default_credentials=True,
    verify_ssl=False,  # For development environments
    timeout=60,  # Request timeout in seconds
    metadata_cache_dir="./my_cache",  # Custom cache directory
    use_label_cache=True,  # Enable label caching
    label_cache_expiry_minutes=120  # Cache for 2 hours
)
```

## Core Operations

### CRUD Operations

```python
async with FOClient(config) as client:
    # CREATE - Create new customer
    new_customer = {
        "CustomerAccount": "US-999",
        "Name": "Test Customer",
        "SalesCurrencyCode": "USD"
    }
    created = await client.create_entity("Customers", new_customer)
    
    # READ - Get single customer
    customer = await client.get_entity("Customers", "US-001")
    
    # UPDATE - Update customer
    updates = {"Name": "Updated Customer Name"}
    updated = await client.update_entity("Customers", "US-001", updates)
    
    # DELETE - Delete customer
    success = await client.delete_entity("Customers", "US-999")
```

### Advanced Querying

```python
from d365fo_client import QueryOptions

# Complex query with multiple options
options = QueryOptions(
    select=["CustomerAccount", "Name", "SalesCurrencyCode", "CustomerGroupId"],
    filter="SalesCurrencyCode eq 'USD' and contains(Name, 'Corp')",
    expand=["CustomerGroup"],
    orderby=["Name desc", "CustomerAccount"],
    top=50,
    skip=10,
    count=True
)

result = await client.get_entities("Customers", options)
print(f"Total count: {result.get('@odata.count')}")
```

### Action Execution

```python
# Unbound action
result = await client.call_action("calculateTax", {
    "amount": 1000.00,
    "taxGroup": "STANDARD"
})

# Bound action on specific entity
result = await client.call_action(
    "calculateBalance",
    parameters={"asOfDate": "2024-12-31"},
    entity_name="Customers", 
    entity_key="US-001"
)
```

### Metadata Operations

```python
# Download and cache metadata
await client.download_metadata(force_refresh=True)

# Search entities
sales_entities = client.search_entities("sales")
print("Sales-related entities:", sales_entities)

# Get detailed entity information
entity_info = client.get_entity_info("Customers")
if entity_info:
    print(f"Entity: {entity_info.name}")
    print(f"Keys: {entity_info.keys}")
    print(f"Properties: {len(entity_info.properties)}")

# Search actions
calc_actions = client.search_actions("calculate")
print("Calculation actions:", calc_actions)
```

### Label Operations

```python
# Get specific label
label_text = await client.get_label_text("@SYS13342")
print(f"Label text: {label_text}")

# Get multiple labels
labels = await client.get_labels_batch([
    "@SYS13342", "@SYS9490", "@GLS63332"
])
for label_id, text in labels.items():
    print(f"{label_id}: {text}")

```
# Enhanced entity info with resolved labels
entity_info = await client.get_entity_info_with_labels("Customers")
if entity_info.label_text:
    print(f"Entity display name: {entity_info.label_text}")

for prop in entity_info.enhanced_properties[:5]:
    if prop.label_text:
        print(f"{prop.name}: {prop.label_text}")
```

## Error Handling

```python
from d365fo_client import FOClientError, EntityError, AuthenticationError

try:
    async with FOClient(config) as client:
        customer = await client.get_entity("Customers", "NON-EXISTENT")
except EntityError as e:
    print(f"Entity operation failed: {e}")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except FOClientError as e:
    print(f"General client error: {e}")
```

## Development

### Setting up Development Environment

```bash
# Clone the repository
git clone https://github.com/mafzaal/d365fo-client.git
cd d365fo-client

# Install with development dependencies
uv sync --dev

# Run tests
uv run pytest

# Format code
uv run black .
uv run isort .

# Type checking
uv run mypy src/
```

### Project Structure

```
d365fo-client/
├── src/
│   └── d365fo_client/
│       ├── __init__.py          # Public API exports
│       ├── client.py            # Main FOClient class
│       ├── models.py            # Data models and configurations
│       ├── auth.py              # Authentication management
│       ├── session.py           # HTTP session management
│       ├── metadata.py          # Metadata operations
│       ├── cache.py             # Label caching
│       ├── crud.py              # CRUD operations
│       ├── labels.py            # Label operations
│       ├── query.py             # OData query utilities
│       ├── exceptions.py        # Custom exceptions
│       ├── main.py              # CLI entry point
│       └── mcp/                 # Model Context Protocol server
│           ├── __init__.py      # MCP server exports
│           ├── server.py        # Main MCP server implementation
│           ├── main.py          # MCP server entry point
│           ├── client_manager.py# Connection pooling for MCP
│           ├── models.py        # MCP-specific data models
│           ├── tools/           # MCP tool implementations
│           │   ├── connection_tools.py
│           │   ├── crud_tools.py
│           │   ├── metadata_tools.py
│           │   └── label_tools.py
│           └── resources/       # MCP resource handlers
│               ├── entity_handler.py
│               ├── metadata_handler.py
│               └── query_handler.py
├── tests/                       # Comprehensive test suite
│   ├── integration/             # Multi-tier integration tests (17 tests - all passing ✅)
│   │   ├── mock_server/         # Mock D365 F&O API server
│   │   ├── test_sandbox.py      # Sandbox environment tests
│   │   ├── test_mock_server.py  # Mock server tests  
│   │   └── README.md           # Integration testing documentation
│   ├── unit/                   # Unit tests
│   └── mcp/                    # MCP server tests (14 tests - all passing ✅)
├── docs/                        # Documentation
├── pyproject.toml               # Project configuration
└── README.md                    # This file
```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `base_url` | str | Required | D365 F&O base URL |
| `client_id` | str | None | Azure AD client ID |
| `client_secret` | str | None | Azure AD client secret |
| `tenant_id` | str | None | Azure AD tenant ID |
| `use_default_credentials` | bool | True | Use Azure Default Credential |
| `verify_ssl` | bool | False | Verify SSL certificates |
| `timeout` | int | 30 | Request timeout in seconds |
| `metadata_cache_dir` | str | Platform-specific user cache | Metadata cache directory |
| `use_label_cache` | bool | True | Enable label caching |
| `label_cache_expiry_minutes` | int | 60 | Label cache expiry time |

### Cache Directory Behavior

By default, the client uses platform-appropriate user cache directories:

- **Windows**: `%LOCALAPPDATA%\d365fo-client` (e.g., `C:\Users\username\AppData\Local\d365fo-client`)
- **macOS**: `~/Library/Caches/d365fo-client` (e.g., `/Users/username/Library/Caches/d365fo-client`)
- **Linux**: `~/.cache/d365fo-client` (e.g., `/home/username/.cache/d365fo-client`)

You can override this by explicitly setting `metadata_cache_dir`:

```python
from d365fo_client import FOClientConfig

# Use custom cache directory
config = FOClientConfig(
    base_url="https://your-fo-environment.dynamics.com",
    metadata_cache_dir="/custom/cache/path"
)

# Or get the default cache directory programmatically
from d365fo_client import get_user_cache_dir

cache_dir = get_user_cache_dir("my-app")  # Platform-appropriate cache dir
config = FOClientConfig(
    base_url="https://your-fo-environment.dynamics.com", 
    metadata_cache_dir=str(cache_dir)
)
```

## Testing

This project includes comprehensive testing at multiple levels to ensure reliability and quality.

### Unit Tests

Run standard unit tests for core functionality:

```bash
# Run all unit tests
uv run pytest

# Run with coverage
uv run pytest --cov=d365fo_client --cov-report=html

# Run specific test file
uv run pytest tests/test_client.py -v
```

### Integration Tests

The project includes a sophisticated multi-tier integration testing framework:

#### Quick Start

```bash
# Run sandbox integration tests (recommended)
.\tests\integration\integration-test-simple.ps1 test-sandbox

# Run mock server tests (no external dependencies)
.\tests\integration\integration-test-simple.ps1 test-mock

# Run with verbose output
.\tests\integration\integration-test-simple.ps1 test-sandbox -VerboseOutput
```

#### Test Levels

1. **Mock Server Tests** - Fast, isolated tests against a simulated D365 F&O API
   - No external dependencies
   - Complete API simulation
   - Ideal for CI/CD pipelines

2. **Sandbox Tests** ⭐ *(Default)* - Tests against real D365 F&O test environments
   - Validates authentication
   - Tests real API behavior
   - Requires test environment access

3. **Live Tests** - Optional tests against production environments
   - Final validation
   - Performance benchmarking
   - Use with caution

#### Configuration

Set up integration testing with environment variables:

```bash
# Copy the template and configure
cp tests/integration/.env.template tests/integration/.env

# Edit .env file with your settings:
INTEGRATION_TEST_LEVEL=sandbox
D365FO_SANDBOX_BASE_URL=https://your-test.dynamics.com
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id
```

#### Available Commands

```bash
# Test environment setup
.\tests\integration\integration-test-simple.ps1 setup

# Dependency checking
.\tests\integration\integration-test-simple.ps1 deps-check

# Run specific test levels
.\tests\integration\integration-test-simple.ps1 test-mock
.\tests\integration\integration-test-simple.ps1 test-sandbox
.\tests\integration\integration-test-simple.ps1 test-live

# Coverage and reporting
.\tests\integration\integration-test-simple.ps1 coverage

# Clean up test artifacts
.\tests\integration\integration-test-simple.ps1 clean
```

#### Test Coverage

Integration tests cover:

- ✅ **Connection & Authentication** - Azure AD integration, SSL/TLS validation
- ✅ **Version Methods** - Application, platform, and build version retrieval
- ✅ **Metadata Operations** - Entity discovery, metadata API validation
- ✅ **Data Operations** - CRUD operations, OData query validation
- ✅ **Error Handling** - Network failures, authentication errors, invalid requests
- ✅ **Performance** - Response time validation, concurrent operations

For detailed information, see [Integration Testing Documentation](tests/integration/README.md).

### Test Results

Recent sandbox integration test results:
```
✅ 17 passed, 0 failed, 2 warnings in 37.67s
====================================================== 
✅ TestSandboxConnection::test_connection_success
✅ TestSandboxConnection::test_metadata_connection_success  
✅ TestSandboxVersionMethods::test_get_application_version
✅ TestSandboxVersionMethods::test_get_platform_build_version
✅ TestSandboxVersionMethods::test_get_application_build_version
✅ TestSandboxVersionMethods::test_version_consistency
✅ TestSandboxMetadataOperations::test_download_metadata
✅ TestSandboxMetadataOperations::test_search_entities
✅ TestSandboxMetadataOperations::test_get_data_entities
✅ TestSandboxMetadataOperations::test_get_public_entities
✅ TestSandboxDataOperations::test_get_available_entities
✅ TestSandboxDataOperations::test_odata_query_options
✅ TestSandboxAuthentication::test_authenticated_requests
✅ TestSandboxErrorHandling::test_invalid_entity_error
✅ TestSandboxErrorHandling::test_invalid_action_error
✅ TestSandboxPerformance::test_response_times
✅ TestSandboxPerformance::test_concurrent_operations
```

## Model Context Protocol (MCP) Server

d365fo-client includes a comprehensive **Model Context Protocol (MCP) server** that exposes the full capabilities of the D365 Finance & Operations client to AI assistants and other MCP-compatible tools. This enables sophisticated Dynamics 365 integration workflows through standardized protocol interactions.

### Overview

The MCP server provides:
- **12 functional tools** covering all major D365 F&O operations
- **4 resource types** with comprehensive metadata exposure  
- **Production-ready** implementation with proper error handling and authentication
- **Performance optimization** with connection pooling and intelligent caching
- **Comprehensive testing** with 14 unit tests (100% pass rate)

### Quick Start

#### Installation and Setup

```bash
# Install d365fo-client with MCP dependencies
pip install d365fo-client

# Set up environment variables
export D365FO_BASE_URL="https://your-environment.dynamics.com"
export AZURE_CLIENT_ID="your-client-id"          # Optional with default credentials
export AZURE_CLIENT_SECRET="your-client-secret"  # Optional with default credentials  
export AZURE_TENANT_ID="your-tenant-id"          # Optional with default credentials

# Start the MCP server
d365fo-mcp-server
```

#### Alternative: Programmatic Usage

```python
from d365fo_client.mcp import D365FOMCPServer

# Create and run server with custom configuration
config = {
    "default_environment": {
        "base_url": "https://your-environment.dynamics.com",
        "use_default_credentials": True
    }
}

server = D365FOMCPServer(config)
await server.run()
```

### MCP Tools

The server provides 12 comprehensive tools organized into functional categories:

#### Connection Tools (2 tools)
- **`d365fo_test_connection`** - Test environment connectivity and health
- **`d365fo_get_environment_info`** - Get comprehensive environment details, versions, and statistics

#### CRUD Operations (5 tools)
- **`d365fo_query_entities`** - Advanced OData querying with filters, selections, and pagination
- **`d365fo_get_entity_record`** - Retrieve specific records by key with expansion options
- **`d365fo_create_entity_record`** - Create new entity records with validation
- **`d365fo_update_entity_record`** - Update existing records with optimistic concurrency
- **`d365fo_delete_entity_record`** - Delete entity records with conflict detection

#### Metadata Tools (3 tools)
- **`d365fo_search_entities`** - Search entities by pattern with advanced filtering
- **`d365fo_get_entity_schema`** - Get detailed entity schemas with properties and relationships
- **`d365fo_search_actions`** - Search available OData actions and functions

#### Label Tools (2 tools)  
- **`d365fo_get_label`** - Get single label text by ID with language support
- **`d365fo_get_labels_batch`** - Get multiple labels efficiently in batch operations

### MCP Resources

The server exposes four types of resources for discovery and access:

#### Entity Resources
Access entity metadata and sample data:
```
d365fo://entities/Customers       # Customer entity with metadata and sample data
d365fo://entities/SalesOrders     # Sales order entity information
d365fo://entities/Products        # Product entity details
```

#### Metadata Resources
Access system-wide metadata:
```
d365fo://metadata/entities        # All data entities metadata
d365fo://metadata/actions         # Available OData actions  
d365fo://metadata/enumerations    # System enumerations
d365fo://metadata/labels          # System labels and translations
```

#### Environment Resources
Access environment status and information:
```
d365fo://environment/status       # Environment health and connectivity
d365fo://environment/version      # Version information
d365fo://environment/cache        # Cache status and statistics
```

#### Query Resources
Access predefined and templated queries:
```
d365fo://queries/customers_recent # Recent customers query template
d365fo://queries/sales_summary    # Sales summary query with parameters
```

### Usage Examples

#### Basic Tool Execution

```json
{
  "tool": "d365fo_query_entities",
  "arguments": {
    "entityName": "Customers",
    "select": ["CustomerAccount", "Name", "Email"],
    "filter": "CustomerGroup eq 'VIP'",
    "top": 10
  }
}
```

#### Entity Schema Discovery

```json
{
  "tool": "d365fo_get_entity_schema", 
  "arguments": {
    "entityName": "SalesOrders",
    "includeProperties": true,
    "resolveLabels": true,
    "language": "en-US"
  }
}
```

#### Environment Information

```json
{
  "tool": "d365fo_get_environment_info",
  "arguments": {}
}
```

### Authentication & Configuration

#### Default Credentials (Recommended)
Uses Azure Default Credential chain (Managed Identity, Azure CLI, etc.):

```bash
export D365FO_BASE_URL="https://your-environment.dynamics.com"
# No additional auth environment variables needed
d365fo-mcp-server
```

#### Explicit Credentials
For service principal authentication:

```bash
export D365FO_BASE_URL="https://your-environment.dynamics.com"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_TENANT_ID="your-tenant-id"
d365fo-mcp-server
```

#### Advanced Configuration

Create a configuration file or set additional environment variables:

```bash
# Optional: Logging configuration
export D365FO_LOG_LEVEL="DEBUG"

# Optional: Cache settings
export D365FO_CACHE_DIR="/custom/cache/path"

# Optional: Performance tuning
export D365FO_CONNECTION_TIMEOUT="60"
export D365FO_MAX_CONCURRENT_REQUESTS="10"
```

### Integration with AI Assistants

The MCP server seamlessly integrates with AI assistants and development tools:

#### Claude Desktop Integration
Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "d365fo": {
      "command": "d365fo-mcp-server",
      "env": {
        "D365FO_BASE_URL": "https://your-environment.dynamics.com"
      }
    }
  }
}
```

#### VS Code Integration
Use with MCP-compatible VS Code extensions for in-editor D365 F&O assistance.

#### Custom MCP Clients
Connect using any MCP-compatible client library:

```python
from mcp import Client

async with Client("d365fo-mcp-server") as client:
    # Discover available tools
    tools = await client.list_tools()
    
    # Execute operations
    result = await client.call_tool(
        "d365fo_query_entities",
        {"entityName": "Customers", "top": 5}
    )
```

### Architecture Benefits

#### For AI Assistants
- **Standardized Interface**: Consistent MCP protocol access to D365 F&O
- **Rich Metadata**: Self-describing entities and operations
- **Type Safety**: Schema validation for all operations
- **Error Context**: Detailed error information for troubleshooting

#### For Developers  
- **Minimal Integration**: Standard MCP client libraries
- **Comprehensive Coverage**: Full D365 F&O functionality exposed
- **Performance Optimized**: Efficient connection and caching strategies
- **Well Documented**: Complete API documentation and examples

#### For Organizations
- **Secure Access**: Enterprise-grade authentication (Azure AD, Managed Identity)
- **Audit Logging**: Complete operation tracking and monitoring
- **Scalable Design**: Connection pooling and session management
- **Maintenance Friendly**: Clear architecture and comprehensive test coverage

### Troubleshooting

#### Common Issues

**Connection Failures**
```bash
# Test connectivity
d365fo-client get-version --base-url https://your-environment.dynamics.com

# Check logs
tail -f ~/.d365fo-mcp/logs/mcp-server.log
```

**Authentication Issues**
```bash
# Verify Azure CLI authentication
az account show

# Test with explicit credentials
export AZURE_CLIENT_ID="your-client-id"
# ... set other variables
d365fo-mcp-server
```

**Performance Issues**
```bash
# Enable debug logging
export D365FO_LOG_LEVEL="DEBUG"

# Adjust connection settings
export D365FO_CONNECTION_TIMEOUT="120"
export D365FO_MAX_CONCURRENT_REQUESTS="5"
```

#### Getting Help

- **Logs**: Check `~/.d365fo-mcp/logs/mcp-server.log` for detailed error information
- **Environment**: Use `d365fo_get_environment_info` tool to check system status
- **Documentation**: See [MCP Implementation Summary](docs/MCP_IMPLEMENTATION_SUMMARY.md) for technical details
- **Issues**: Report problems at [GitHub Issues](https://github.com/mafzaal/d365fo-client/issues)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`uv run pytest`)
5. Run integration tests (`.\tests\integration\integration-test-simple.ps1 test-sandbox`)
6. Format code (`uv run black . && uv run isort .`)
7. Commit changes (`git commit -m 'Add amazing feature'`)
8. Push to branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes and version history.

## Support

- 📧 Email: mo@thedataguy.pro
- 🐛 Issues: [GitHub Issues](https://github.com/mafzaal/d365fo-client/issues)


## Related Projects

- [Microsoft Dynamics 365](https://dynamics.microsoft.com/)
- [OData](https://www.odata.org/)
- [Azure Identity](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/identity/azure-identity)
- [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol/python-sdk) - For AI assistant integration
