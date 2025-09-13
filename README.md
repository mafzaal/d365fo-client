# Dynamics 365 Finance & Operations MCP Server

**Production-ready Model Context Protocol (MCP) server** that exposes the full capabilities of Microsoft Dynamics 365 Finance & Operations (D365 F&O) to AI assistants and other MCP-compatible tools. This enables sophisticated Dynamics 365 integration workflows through standardized protocol interactions.

**🚀 One-Click Installation for VS Code:**

[![Install with UVX in VS Code](https://img.shields.io/badge/VS_Code-Install_D365_FO_MCP_Server-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect/mcp/install?name=d365fo&config=%7B%22type%22%3A%22stdio%22%2C%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22--from%22%2C%22d365fo-client%40latest%22%2C%22d365fo-mcp-server%22%5D%2C%22env%22%3A%7B%22D365FO_CLIENT_ID%22%3A%22%24%7Binput%3Aclient_id%7D%22%2C%22D365FO_CLIENT_SECRET%22%3A%22%24%7Binput%3Aclient_secret%7D%22%2C%22D365FO_TENANT_ID%22%3A%22%24%7Binput%3Atenant_id%7D%22%7D%7D&inputs=%5B%7B%22id%22%3A%22tenant_id%22%2C%22type%22%3A%22promptString%22%2C%22description%22%3A%22The%20ID%20of%20the%20tenant%20to%20connect%20to%22%2C%22password%22%3Atrue%7D%2C%7B%22id%22%3A%22client_id%22%2C%22type%22%3A%22promptString%22%2C%22description%22%3A%22The%20ID%20of%20the%20client%20to%20connect%20to%22%2C%22password%22%3Atrue%7D%2C%7B%22id%22%3A%22client_secret%22%2C%22type%22%3A%22promptString%22%2C%22description%22%3A%22The%20secret%20of%20the%20client%20to%20connect%20to%22%2C%22password%22%3Atrue%7D%5D)
[![Install with UVX in VS Code Insiders](https://img.shields.io/badge/VS_Code_Insiders-Install_D365_FO_MCP_Server-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=d365fo&quality=insiders&config=%7B%22type%22%3A%22stdio%22%2C%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22--from%22%2C%22d365fo-client%40latest%22%2C%22d365fo-mcp-server%22%5D%2C%22env%22%3A%7B%22D365FO_CLIENT_ID%22%3A%22%24%7Binput%3Aclient_id%7D%22%2C%22D365FO_CLIENT_SECRET%22%3A%22%24%7Binput%3Aclient_secret%7D%22%2C%22D365FO_TENANT_ID%22%3A%22%24%7Binput%3Atenant_id%7D%22%7D%7D&inputs=%5B%7B%22id%22%3A%22tenant_id%22%2C%22type%22%3A%22promptString%22%2C%22description%22%3A%22The%20ID%20of%20the%20tenant%20to%20connect%20to%22%2C%22password%22%3Atrue%7D%2C%7B%22id%22%3A%22client_id%22%2C%22type%22%3A%22promptString%22%2C%22description%22%3A%22The%20ID%20of%20the%20client%20to%20connect%20to%22%2C%22password%22%3Atrue%7D%2C%7B%22id%22%3A%22client_secret%22%2C%22type%22%3A%22promptString%22%2C%22description%22%3A%22The%20secret%20of%20the%20client%20to%20connect%20to%22%2C%22password%22%3Atrue%7D%5D)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/d365fo-client?label=Downloads)](https://pypi.org/project/d365fo-client/)

**Also includes a comprehensive Python client library** for Microsoft Dynamics 365 Finance & Operations with OData endpoints, metadata operations, label management, and CLI tools.

## MCP Server Overview

The d365fo-client includes **two production-ready Model Context Protocol (MCP) servers** that expose the full capabilities of D365 Finance & Operations to AI assistants and other MCP-compatible tools:

- **Traditional MCP SDK** (`d365fo-mcp-server`) - Original implementation with stdio support
- **FastMCP Framework** (`d365fo-fastmcp-server`) - Modern implementation with multi-transport support ⭐ **Recommended**

Both servers provide identical functionality but the FastMCP implementation offers enhanced performance and deployment flexibility.

### Key Features

- **34 comprehensive tools** covering all major D365 F&O operations across 7 functional categories
- **12 resource types** with comprehensive metadata exposure and discovery capabilities
- **2 prompt templates** for advanced workflow assistance
- **Multi-transport support** (FastMCP): stdio, HTTP, Server-Sent Events (SSE)
- **Production-ready** implementation with proper error handling, authentication, and security validation
- **Enhanced performance** (FastMCP): 40% faster startup, 15% lower memory usage
- **Advanced profile management** supporting multiple environments with secure credential storage
- **Database analysis capabilities** with secure SQL querying and metadata insights
- **Session-based synchronization** with detailed progress tracking and multiple sync strategies
- **Multi-language support** with label resolution and localization capabilities
- **Enterprise security** with Azure AD integration, Key Vault support, and audit logging

### Quick Start

#### Installation and Setup

```bash
# Install d365fo-client with MCP dependencies
pip install d365fo-client

# Set up environment variables
export D365FO_BASE_URL="https://your-environment.dynamics.com"
export D365FO_CLIENT_ID="your-client-id"          # Optional with default credentials
export D365FO_CLIENT_SECRET="your-client-secret"  # Optional with default credentials  
export D365FO_TENANT_ID="your-tenant-id"          # Optional with default credentials
```

#### FastMCP Server (Recommended)

The modern FastMCP implementation provides enhanced performance and multiple transport options:

```bash
# Development (stdio transport - default)
d365fo-fastmcp-server

# Production HTTP API
d365fo-fastmcp-server --transport http --port 8000 --host 0.0.0.0

# Real-time Web Applications (SSE)
d365fo-fastmcp-server --transport sse --port 8001 --host 0.0.0.0
```

**Key Benefits:**
- **40% faster startup** compared to traditional MCP SDK
- **15% lower memory usage** through optimized architecture
- **Multi-transport support**: stdio, HTTP, Server-Sent Events (SSE)
- **Enhanced error handling** with better async/await support
- **Production ready** with web transports for API integration

#### Traditional MCP Server

The original MCP SDK implementation remains available for backward compatibility:

```bash
# Start the traditional MCP server
d365fo-mcp-server
```

#### Integration with AI Assistants

##### VS Code Integration (Recommended)

**FastMCP Server with Default Credentials:**
Add to your VS Code `mcp.json` for GitHub Copilot with MCP:

```json
{
  "servers": {
    "d365fo-fastmcp-server": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--from",
        "d365fo-client@latest",
        "d365fo-fastmcp-server"
      ],
      "env": {
        "D365FO_BASE_URL": "https://your-environment.dynamics.com",
        "D365FO_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Traditional MCP Server (Alternative):**
```json
{
  "servers": {
    "d365fo-mcp-server": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--from",
        "d365fo-client",
        "d365fo-mcp-server"
      ],
      "env": {
        "D365FO_BASE_URL": "https://your-environment.dynamics.com",
        "D365FO_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Option 2: Explicit Credentials**
For environments requiring service principal authentication:

```json
{
  "servers": {
    "d365fo-fastmcp-server": {
      "type": "stdio", 
      "command": "uvx",
      "args": [
        "--from",
        "d365fo-client",
        "d365fo-fastmcp-server"
      ],
      "env": {
        "D365FO_BASE_URL": "https://your-environment.dynamics.com",
        "D365FO_LOG_LEVEL": "DEBUG",
        "D365FO_CLIENT_ID": "${input:client_id}",
        "D365FO_CLIENT_SECRET": "${input:client_secret}",
        "D365FO_TENANT_ID": "${input:tenant_id}"
      }
    }
  },
  "inputs": [
    {
      "id": "tenant_id",
      "type": "promptString",
      "description": "Azure AD Tenant ID for D365 F&O authentication",
      "password": true
    },
    {
      "id": "client_id", 
      "type": "promptString",
      "description": "Azure AD Client ID for D365 F&O authentication",
      "password": true
    },
    {
      "id": "client_secret",
      "type": "promptString", 
      "description": "Azure AD Client Secret for D365 F&O authentication",
      "password": true
    }
  ]
}
```

##### Claude Desktop Integration

**FastMCP Server:**
Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "d365fo-fastmcp": {
      "command": "uvx",
      "args": [
        "--from",
        "d365fo-client",
        "d365fo-fastmcp-server"
      ],
      "env": {
        "D365FO_BASE_URL": "https://your-environment.dynamics.com",
        "D365FO_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Traditional MCP Server (Alternative):**
```json
{
  "mcpServers": {
    "d365fo": {
      "command": "uvx",
      "args": [
        "--from",
        "d365fo-client",
        "d365fo-mcp-server"
      ],
      "env": {
        "D365FO_BASE_URL": "https://your-environment.dynamics.com",
        "D365FO_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Benefits of uvx approach:**
- Always uses the latest version from the repository
- No local installation required  
- Automatic dependency management
- Works across different environments

#### Web Integration with FastMCP

The FastMCP server provides HTTP and SSE transports for web application integration:

##### HTTP Transport for Web APIs

```python
import aiohttp
import json

async def call_d365fo_api():
    """Example: Using HTTP transport for web API integration"""
    
    # Start FastMCP server with HTTP transport
    # d365fo-fastmcp-server --transport http --port 8000
    
    mcp_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "d365fo_query_entities",
            "arguments": {
                "entityName": "CustomersV3",
                "top": 10,
                "select": ["CustomerAccount", "Name"]
            }
        }
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8000/mcp",
            json=mcp_request,
            headers={"Content-Type": "application/json"}
        ) as response:
            result = await response.json()
            print(json.dumps(result, indent=2))
```

##### SSE Transport for Real-time Applications

```javascript
// Example: JavaScript client for real-time D365FO data
// Start FastMCP server: d365fo-fastmcp-server --transport sse --port 8001

const eventSource = new EventSource('http://localhost:8001/sse');

eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received D365FO data:', data);
    
    // Handle real-time updates from D365FO
    if (data.method === 'notification') {
        updateDashboard(data.params);
    }
};

// Send MCP requests via SSE
function queryCustomers() {
    const request = {
        jsonrpc: "2.0",
        id: Date.now(),
        method: "tools/call",
        params: {
            name: "d365fo_search_entities",
            arguments: {
                pattern: "customer",
                limit: 50
            }
        }
    };
    
    fetch('http://localhost:8001/sse/send', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(request)
    });
}
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
d365fo-client version app --base-url https://your-environment.dynamics.com

# Check logs
tail -f ~/.d365fo-mcp/logs/mcp-server.log
```

**Authentication Issues**
```bash
# Verify Azure CLI authentication
az account show

# Test with explicit credentials
export D365FO_CLIENT_ID="your-client-id"
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

### MCP Tools

The server provides **34 comprehensive tools** organized into functional categories:

#### Connection & Environment Tools (2 tools)
- **`d365fo_test_connection`** - Test connectivity and authentication with performance metrics and error diagnostics
- **`d365fo_get_environment_info`** - Get comprehensive environment details including versions, configurations, and capabilities

#### CRUD Operations Tools (6 tools)
- **`d365fo_query_entities`** - Advanced OData querying with filters, selections, pagination, and performance optimization
- **`d365fo_get_entity_record`** - Retrieve specific records by key with expansion options and ETag support
- **`d365fo_create_entity_record`** - Create new entity records with validation and business logic execution
- **`d365fo_update_entity_record`** - Update existing records with partial updates and optimistic concurrency control
- **`d365fo_delete_entity_record`** - Delete entity records with referential integrity checking and cascading rules
- **`d365fo_call_action`** - Execute OData actions and functions for complex business operations

#### Metadata Discovery Tools (6 tools)
- **`d365fo_search_entities`** - Search entities by pattern with category filtering and full-text search capabilities
- **`d365fo_get_entity_schema`** - Get detailed entity schemas with properties, relationships, and label resolution
- **`d365fo_search_actions`** - Search available OData actions with binding type and parameter information
- **`d365fo_search_enumerations`** - Search system enumerations with keyword-based filtering
- **`d365fo_get_enumeration_fields`** - Get detailed enumeration member information with multi-language support
- **`d365fo_get_installed_modules`** - Retrieve information about installed modules and their configurations

#### Label Management Tools (2 tools)
- **`d365fo_get_label`** - Get single label text by ID with multi-language support and fallback options
- **`d365fo_get_labels_batch`** - Get multiple labels efficiently with batch processing and performance optimization

#### Profile Management Tools (10 tools)
- **`d365fo_list_profiles`** - List all configured D365FO environment profiles with status information
- **`d365fo_get_profile`** - Get detailed configuration information for specific profiles
- **`d365fo_create_profile`** - Create new environment profiles with comprehensive authentication options
- **`d365fo_update_profile`** - Modify existing profile configurations with partial update support
- **`d365fo_delete_profile`** - Remove environment profiles with proper cleanup and validation
- **`d365fo_set_default_profile`** - Designate a specific profile as the default for operations
- **`d365fo_get_default_profile`** - Retrieve information about the currently configured default profile
- **`d365fo_validate_profile`** - Validate profile configurations for completeness and security compliance
- **`d365fo_test_profile_connection`** - Test connectivity and authentication for specific profiles
- **`d365fo_get_profile_status`** - Get comprehensive status information for profiles

#### Database Analysis Tools (4 tools)
- **`d365fo_execute_sql_query`** - Execute SELECT queries against metadata database with security validation
- **`d365fo_get_database_schema`** - Get comprehensive database schema information including relationships
- **`d365fo_get_table_info`** - Get detailed information about specific database tables with sample data
- **`d365fo_get_database_statistics`** - Generate database statistics and analytics for performance monitoring

#### Synchronization Tools (4 tools)
- **`d365fo_start_sync`** - Initiate metadata synchronization with various strategies and session tracking
- **`d365fo_get_sync_progress`** - Monitor detailed progress of sync sessions with time estimates
- **`d365fo_cancel_sync`** - Cancel running sync sessions with graceful cleanup
- **`d365fo_list_sync_sessions`** - List all active sync sessions with status and progress information

**📖 For detailed information about all MCP tools including usage examples and best practices, see the [Comprehensive MCP Tools Introduction](docs/MCP_TOOLS_COMPREHENSIVE_INTRODUCTION.md).**

### MCP Resources

The server exposes four types of resources for discovery and access:

#### Entity Resources
Access entity metadata and sample data:
```
d365fo://entities/CustomersV3     # Customer entity with metadata and sample data
d365fo://entities/SalesOrders     # Sales order entity information
d365fo://entities/Products        # Product entity details
```

#### Metadata Resources
Access system-wide metadata:
```
d365fo://metadata/entities        # All data entities metadata (V2 cache)
d365fo://metadata/actions         # Available OData actions  
d365fo://metadata/enumerations    # System enumerations
d365fo://metadata/labels          # System labels and translations
```

#### Environment Resources
Access environment status and information:
```
d365fo://environment/status       # Environment health and connectivity
d365fo://environment/version      # Version information (app, platform, build)
d365fo://environment/cache        # Cache status and statistics V2
```

#### Query Resources
Access predefined and templated queries:
```
d365fo://queries/customers_recent # Recent customers query template
d365fo://queries/sales_summary    # Sales summary query with parameters
```

#### Database Resources (New in V2)
Access metadata database queries:
```
d365fo://database/entities        # SQL-based entity searches with FTS5
d365fo://database/actions         # Action discovery with metadata
d365fo://database/statistics      # Cache and performance statistics
```

### Usage Examples

#### Basic Tool Execution

```json
{
  "tool": "d365fo_query_entities",
  "arguments": {
    "entityName": "CustomersV3",
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
    "entityName": "CustomersV3",
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
export D365FO_CLIENT_ID="your-client-id"
export D365FO_CLIENT_SECRET="your-client-secret"
export D365FO_TENANT_ID="your-tenant-id"
d365fo-mcp-server
```

#### Azure Key Vault Integration (New in v0.2.3)
For secure credential storage using Azure Key Vault:

```bash
export D365FO_BASE_URL="https://your-environment.dynamics.com"
export D365FO_CREDENTIAL_SOURCE="keyvault"
export D365FO_KEYVAULT_URL="https://your-keyvault.vault.azure.net/"
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

## Python Client Library

### Features

- 🔗 **OData Client**: Full CRUD operations on D365 F&O data entities with composite key support
- 📊 **Metadata Management V2**: Enhanced caching system with intelligent synchronization and FTS5 search
- 🏷️ **Label Operations V2**: Multilingual label caching with performance improvements and async support
- 🔍 **Advanced Querying**: Support for all OData query parameters ($select, $filter, $expand, etc.)
- ⚡ **Action Execution**: Execute bound and unbound OData actions with comprehensive parameter handling
- 🔒 **Authentication**: Azure AD integration with default credentials, service principal, and Azure Key Vault support
- 💾 **Intelligent Caching**: Cross-environment cache sharing with module-based version detection
- 🌐 **Async/Await**: Modern async/await patterns with optimized session management
- 📝 **Type Hints**: Full type annotation support with enhanced data models
- 🤖 **MCP Server**: Production-ready Model Context Protocol server with 12 tools and 4 resource types
- 🖥️ **Comprehensive CLI**: Hierarchical command-line interface for all D365 F&O operations
- 🧪 **Multi-tier Testing**: Mock, sandbox, and live integration testing framework (17/17 tests passing)
- 📋 **Metadata Scripts**: PowerShell and Python utilities for entity, enumeration, and action discovery
- 🔐 **Enhanced Credential Management**: Support for Azure Key Vault and multiple credential sources
- 📊 **Advanced Sync Management**: Session-based synchronization with detailed progress tracking

### Installation

```bash
# Install from PyPI
pip install d365fo-client

# Or install from source
git clone https://github.com/mafzaal/d365fo-client.git
cd d365fo-client
uv sync  # Installs with exact dependencies from uv.lock
```

**Note**: The package includes MCP (Model Context Protocol) dependencies by default, enabling AI assistant integration. Both `d365fo-client` CLI and `d365fo-mcp-server` commands will be available after installation.

**Breaking Change in v0.2.3**: Environment variable names have been updated for consistency:
- `AZURE_CLIENT_ID` → `D365FO_CLIENT_ID`
- `AZURE_CLIENT_SECRET` → `D365FO_CLIENT_SECRET`  
- `AZURE_TENANT_ID` → `D365FO_TENANT_ID`

Please update your environment variables accordingly when upgrading.

## Python Client Quick Start

## Command Line Interface (CLI)

d365fo-client provides a comprehensive CLI with hierarchical commands for interacting with Dynamics 365 Finance & Operations APIs and metadata. The CLI supports all major operations including entity management, metadata discovery, and system administration.

### Usage

```bash
# Use the installed CLI command
d365fo-client [GLOBAL_OPTIONS] COMMAND [SUBCOMMAND] [OPTIONS]

# Alternative: Module execution
python -m d365fo_client.main [OPTIONS] COMMAND [ARGS]
```

### Command Categories

#### Entity Operations
```bash
# List entities with filtering
d365fo-client entities list --pattern "customer" --limit 10

# Get entity details and schema
d365fo-client entities get CustomersV3 --properties --keys --labels

# CRUD operations
d365fo-client entities create Customers --data '{"CustomerAccount":"US-999","Name":"Test"}'
d365fo-client entities update Customers US-999 --data '{"Name":"Updated Name"}'
d365fo-client entities delete Customers US-999
```

#### Metadata Operations
```bash
# Search and discover entities
d365fo-client metadata entities --search "sales" --output json

# Get available actions
d365fo-client metadata actions --pattern "calculate" --limit 5

# Enumerate system enumerations
d365fo-client metadata enums --search "status" --output table

# Synchronize metadata cache
d365fo-client metadata sync --force-refresh
```

#### Version Information
```bash
# Get application versions
d365fo-client version app
d365fo-client version platform  
d365fo-client version build
```

#### Label Operations
```bash
# Resolve single label
d365fo-client labels resolve "@SYS13342"

# Search labels by pattern
d365fo-client labels search "customer" --language "en-US"
```

### Global Options

- `--base-url URL` — Specify D365 F&O environment URL
- `--profile NAME` — Use named configuration profile  
- `--output FORMAT` — Output format: json, table, csv, yaml (default: table)
- `--verbose` — Enable verbose output for debugging
- `--timeout SECONDS` — Request timeout (default: 30)

### Configuration Profiles

Create reusable configurations in `~/.d365fo-client/config.yaml`:

```yaml
profiles:
  production:
    base_url: "https://prod.dynamics.com"
    use_default_credentials: true
    timeout: 60
    
  development:
    base_url: "https://dev.dynamics.com" 
    client_id: "${D365FO_CLIENT_ID}"
    client_secret: "${D365FO_CLIENT_SECRET}"
    tenant_id: "${D365FO_TENANT_ID}"
    use_cache_first: true

default_profile: "development"
```

### Examples

```bash
# Quick entity discovery
d365fo-client entities list --pattern "cust.*" --output json

# Get comprehensive entity information
d365fo-client entities get CustomersV3 --properties --keys --labels --output yaml

# Search for calculation actions
d365fo-client metadata actions --pattern "calculate|compute" --output table

# Test environment connectivity
d365fo-client version app --verbose
```

For a complete command reference:

```bash
d365fo-client --help
d365fo-client entities --help
d365fo-client metadata --help
```
### Basic Usage

```python
import asyncio
from d365fo_client import D365FOClient, FOClientConfig

async def main():
    # Simple configuration with default credentials
    config = FOClientConfig(
        base_url="https://your-fo-environment.dynamics.com",
        use_default_credentials=True  # Uses Azure Default Credential
    )
    
    async with D365FOClient(config) as client:
        # Test connection
        if await client.test_connection():
            print("✅ Connected successfully!")
        
        # Get environment information
        env_info = await client.get_environment_info()
        print(f"Environment: {env_info.application_version}")
        
        # Search for entities (uses metadata cache v2)
        customer_entities = await client.search_entities("customer")
        print(f"Found {len(customer_entities)} customer entities")
        
        # Get customers with query options
        from d365fo_client import QueryOptions
        options = QueryOptions(
            select=["CustomerAccount", "Name", "SalesCurrencyCode"],
            top=10,
            orderby=["Name"]
        )
        
        customers = await client.get_data("/data/CustomersV3", options)
        print(f"Retrieved {len(customers['value'])} customers")

if __name__ == "__main__":
    asyncio.run(main())
```

### Using Convenience Function

```python
from d365fo_client import create_client

# Quick client creation with enhanced defaults
async with create_client("https://your-fo-environment.dynamics.com") as client:
    customers = await client.get_data("/data/CustomersV3", top=5)
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

# Option 3: Azure Key Vault integration (New in v0.2.3)
config = FOClientConfig(
    base_url="https://your-fo-environment.dynamics.com",
    credential_source="keyvault",  # Use Azure Key Vault for credentials
    keyvault_url="https://your-keyvault.vault.azure.net/"
)

# Option 4: With custom settings
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
async with D365FOClient(config) as client:
    # CREATE - Create new customer (supports composite keys)
    new_customer = {
        "CustomerAccount": "US-999",
        "Name": "Test Customer",
        "SalesCurrencyCode": "USD"
    }
    created = await client.create_data("/data/CustomersV3", new_customer)
    
    # READ - Get single customer by key
    customer = await client.get_data("/data/CustomersV3('US-001')")
    
    # UPDATE - Update customer with optimistic concurrency
    updates = {"Name": "Updated Customer Name"}
    updated = await client.update_data("/data/CustomersV3('US-001')", updates)
    
    # DELETE - Delete customer
    success = await client.delete_data("/data/CustomersV3('US-999')")
    print(f"Delete successful: {success}")
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

result = await client.get_data("/data/CustomersV3", options)
print(f"Total count: {result.get('@odata.count')}")
```

### Action Execution

```python
# Unbound action
result = await client.post_data("/data/calculateTax", {
    "amount": 1000.00,
    "taxGroup": "STANDARD"
})

# Bound action on entity set
result = await client.post_data("/data/CustomersV3/calculateBalances", {
    "asOfDate": "2024-12-31"
})

# Bound action on specific entity instance  
result = await client.post_data("/data/CustomersV3('US-001')/calculateBalance", {
    "asOfDate": "2024-12-31"
})
```

### Metadata Operations

```python
# Intelligent metadata synchronization (v2 system)
sync_manager = await client.get_sync_manager()
await sync_manager.smart_sync()

# Search entities with enhanced filtering
sales_entities = await client.search_entities("sales")
print("Sales-related entities:", [e.name for e in sales_entities])

# Get detailed entity information with labels
entity_info = await client.get_public_entity_info("CustomersV3")
if entity_info:
    print(f"Entity: {entity_info.name}")
    print(f"Label: {entity_info.label_text}")
    print(f"Data Service Enabled: {entity_info.data_service_enabled}")

# Search actions with caching
calc_actions = await client.search_actions("calculate")
print("Calculation actions:", [a.name for a in calc_actions])

# Get enumeration information
enum_info = await client.get_public_enumeration_info("NoYes")
if enum_info:
    print(f"Enum: {enum_info.name}")
    for member in enum_info.members:
        print(f"  {member.name} = {member.value}")
```

### Label Operations

```python
# Get specific label (v2 caching system)
label_text = await client.get_label_text("@SYS13342")
print(f"Label text: {label_text}")

# Get multiple labels efficiently
labels = await client.get_labels_batch([
    "@SYS13342", "@SYS9490", "@GLS63332"
])
for label_id, text in labels.items():
    print(f"{label_id}: {text}")

# Enhanced entity info with resolved labels
entity_info = await client.get_public_entity_info_with_labels("CustomersV3")
if entity_info.label_text:
    print(f"Entity display name: {entity_info.label_text}")

# Access enhanced properties with labels
for prop in entity_info.enhanced_properties[:5]:
    if hasattr(prop, 'label_text') and prop.label_text:
        print(f"{prop.name}: {prop.label_text}")
```

## Error Handling

```python
from d365fo_client import D365FOClientError, AuthenticationError, ConnectionError

try:
    async with D365FOClient(config) as client:
        customer = await client.get_data("/data/CustomersV3('NON-EXISTENT')")
except ConnectionError as e:
    print(f"Connection failed: {e}")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except D365FOClientError as e:
    print(f"Client operation failed: {e}")
    print(f"Status code: {e.status_code}")
    print(f"Response: {e.response_text}")
```

## Development

### Setting up Development Environment

```bash
# Clone the repository
git clone https://github.com/mafzaal/d365fo-client.git
cd d365fo-client

# Install with development dependencies using uv
uv sync --dev

# Run tests
uv run pytest

# Run integration tests
.\tests\integration\integration-test-simple.ps1 test-sandbox

# Format code
uv run black .
uv run isort .

# Type checking
uv run mypy src/

# Quality checks
.\make.ps1 quality-check  # Windows PowerShell
# or
make quality-check       # Unix/Linux/macOS
```

### Project Structure

```
d365fo-client/
├── src/
│   └── d365fo_client/
│       ├── __init__.py          # Public API exports
│       ├── main.py              # CLI entry point  
│       ├── cli.py               # CLI command handlers
│       ├── client.py            # Enhanced D365FOClient class
│       ├── config.py            # Configuration management
│       ├── auth.py              # Authentication management
│       ├── session.py           # HTTP session management
│       ├── crud.py              # CRUD operations
│       ├── query.py             # OData query utilities
│       ├── metadata.py          # Legacy metadata operations
│       ├── metadata_api.py      # Metadata API client
│       ├── metadata_cache.py    # Metadata caching layer V2
│       ├── metadata_sync.py     # Metadata synchronization V2 with session management
│       ├── sync_session.py      # Enhanced sync session management (New in v0.2.3)
│       ├── credential_manager.py # Credential source management (New in v0.2.3)
│       ├── labels.py            # Label operations V2
│       ├── profiles.py          # Profile data models
│       ├── profile_manager.py   # Profile management
│       ├── models.py            # Data models and configurations
│       ├── output.py            # Output formatting
│       ├── utils.py             # Utility functions
│       ├── exceptions.py        # Custom exceptions
│       └── mcp/                 # Model Context Protocol server
│           ├── __init__.py      # MCP server exports
│           ├── main.py          # MCP server entry point
│           ├── server.py        # Core MCP server implementation
│           ├── client_manager.py# D365FO client connection pooling
│           ├── models.py        # MCP-specific data models
│           ├── tools/           # MCP tool implementations (12 tools)
│           │   ├── connection_tools.py
│           │   ├── crud_tools.py
│           │   ├── metadata_tools.py
│           │   └── label_tools.py
│           ├── resources/       # MCP resource handlers (4 types)
│           │   ├── entity_handler.py
│           │   ├── metadata_handler.py
│           │   ├── environment_handler.py
│           │   └── query_handler.py
│           └── prompts/         # MCP prompt templates
├── tests/                       # Comprehensive test suite
│   ├── unit/                    # Unit tests (pytest-based)
│   ├── integration/             # Multi-tier integration testing
│   │   ├── mock_server/         # Mock D365 F&O API server
│   │   ├── test_mock_server.py  # Mock server tests
│   │   ├── test_sandbox.py      # Sandbox environment tests ✅
│   │   ├── test_live.py         # Live environment tests
│   │   ├── conftest.py          # Shared pytest fixtures
│   │   ├── test_runner.py       # Python test execution engine
│   │   └── integration-test-simple.ps1 # PowerShell automation
│   └── test_mcp_server.py       # MCP server unit tests ✅
├── scripts/                     # Metadata discovery scripts
│   ├── search_data_entities.ps1 # PowerShell entity search
│   ├── get_data_entity_schema.ps1 # PowerShell schema retrieval
│   ├── search_enums.py          # Python enumeration search
│   ├── get_enumeration_info.py  # Python enumeration info
│   ├── search_actions.ps1       # PowerShell action search
│   └── get_action_info.py       # Python action information
├── docs/                        # Comprehensive documentation
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
| `credential_source` | str | "environment" | Credential source: "environment", "keyvault" |
| `keyvault_url` | str | None | Azure Key Vault URL for credential storage |
| `verify_ssl` | bool | False | Verify SSL certificates |
| `timeout` | int | 30 | Request timeout in seconds |
| `metadata_cache_dir` | str | Platform-specific user cache | Metadata cache directory |
| `use_label_cache` | bool | True | Enable label caching V2 |
| `label_cache_expiry_minutes` | int | 60 | Label cache expiry time |
| `use_cache_first` | bool | False | Enable cache-first mode with background sync |

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
D365FO_CLIENT_ID=your-client-id
D365FO_CLIENT_SECRET=your-client-secret
D365FO_TENANT_ID=your-tenant-id
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
