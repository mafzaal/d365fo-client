# MCP Server for d365fo-client

This directory contains the Model Context Protocol (MCP) server implementation for d365fo-client, enabling AI assistants and other MCP-compatible tools to interact with Microsoft Dynamics 365 Finance & Operations environments.

## Quick Start

### Installation
```bash
# Install d365fo-client with MCP support
pip install d365fo-client[mcp]
```

### Configuration
Set environment variables for your D365FO environment:
```bash
export D365FO_BASE_URL="https://your-d365fo-environment.dynamics.com"
export D365FO_CLIENT_ID="your-client-id"
export D365FO_CLIENT_SECRET="your-client-secret"  
export D365FO_TENANT_ID="your-tenant-id"
```

Or use default credentials (recommended for Azure environments):
```bash
export D365FO_BASE_URL="https://your-d365fo-environment.dynamics.com"
# Default credentials will be used automatically
```

### Running the MCP Server
```bash
# Start the MCP server with stdio transport
d365fo-fastmcp-server
```

## Architecture

The MCP server exposes d365fo-client capabilities through:

### Resources
- **Entity Resources** (`d365fo://entities/{name}`) - Entity metadata and sample data
- **Metadata Resources** (`d365fo://metadata/{type}`) - System metadata (entities, actions, enumerations, labels)  
- **Environment Resources** (`d365fo://environment/{aspect}`) - Environment status, version info, cache statistics
- **Query Resources** (`d365fo://queries/{name}`) - Predefined query templates

### Tools
- **Connection Tools** - Test connectivity, get environment info
- **CRUD Tools** - Query, create, update, delete entity records
- **Metadata Tools** - Search entities/actions, get entity schemas  
- **Label Tools** - Retrieve system labels and translations

## Usage Examples

### With MCP-Compatible Clients

Once the server is running, MCP clients can discover and use the available tools:

```python
# Example: Query customer entities
{
  "tool": "d365fo_query_entities",
  "arguments": {
    "entityName": "Customers",
    "select": ["CustomerAccount", "Name", "Email"],
    "filter": "CustomerGroup eq 'VIP'",
    "top": 10
  }
}

# Example: Get entity schema
{
  "tool": "d365fo_get_entity_schema", 
  "arguments": {
    "entityName": "SalesOrders",
    "includeProperties": true,
    "resolveLabels": true
  }
}

# Example: Test connection
{
  "tool": "d365fo_test_connection",
  "arguments": {}
}
```

### Available Resources

List all available resources:
```bash
# Resources are automatically discovered by MCP clients
# Examples include:
# - d365fo://entities/Customers
# - d365fo://metadata/entities  
# - d365fo://environment/status
# - d365fo://queries/customers_recent
```

## Configuration

### Environment Variables
- `D365FO_BASE_URL` - D365FO environment URL
- `D365FO_CLIENT_ID` - Azure AD application client ID (optional with default credentials)
- `D365FO_CLIENT_SECRET` - Azure AD application secret (optional with default credentials)
- `D365FO_TENANT_ID` - Azure AD tenant ID (optional with default credentials)
- `D365FO_CACHE_DIR` - Cache directory (default: `~/.d365fo-mcp/cache`)
- `D365FO_LOG_LEVEL` - Logging level (default: INFO)
- `D365FO_LOG_FILE` - Custom log file path (default: `~/.d365fo-mcp/logs/{server}.log`)

### Authentication
The server supports multiple authentication methods:
1. **Default Credentials** (recommended) - Uses Azure CLI, Managed Identity, etc.
2. **Client Credentials** - Uses explicit client ID/secret
3. **Environment Variables** - Automatic detection from environment

## Development

### Project Structure
```
src/d365fo_client/mcp/
├── __init__.py           # Package exports
├── server.py             # Main MCP server  
├── fastmcp_server.py     # FastMCP server (recommended)
├── client_manager.py     # D365FO client management
├── models.py             # MCP-specific data models
├── main.py               # Entry point script
├── fastmcp_main.py       # FastMCP entry point
├── resources/            # Resource handlers
│   ├── entity_handler.py
│   ├── metadata_handler.py
│   ├── environment_handler.py
│   └── query_handler.py
├── mixins/               # FastMCP tool mixins (recommended)
│   ├── connection_tools_mixin.py
│   ├── crud_tools_mixin.py
│   ├── metadata_tools_mixin.py
│   ├── label_tools_mixin.py
│   ├── profile_tools_mixin.py
│   ├── database_tools_mixin.py
│   ├── sync_tools_mixin.py
│   ├── srs_tools_mixin.py
│   └── performance_tools_mixin.py
└── tools/                # Legacy tool handlers (deprecated)
    ├── connection_tools.py
    ├── crud_tools.py
    ├── metadata_tools.py
    └── label_tools.py
```

### Testing
```bash
# Run MCP server tests
pytest tests/test_mcp_server.py

# Run with coverage
pytest tests/test_mcp_server.py --cov=d365fo_client.mcp
```

## Troubleshooting

### Common Issues

1. **Connection Failures**
   - Verify D365FO_BASE_URL is correct
   - Check Azure authentication credentials
   - Ensure network connectivity to D365FO environment

2. **Permission Errors**
   - Verify Azure AD application has appropriate permissions
   - Check D365FO security roles and access

3. **Cache Issues**
   - Clear cache directory: `rm -rf ~/.d365fo-mcp/cache`
   - Check disk space and permissions

### Debug Mode
```bash
export D365FO_LOG_LEVEL=DEBUG
d365fo-fastmcp-server
```

## Contributing

The MCP server implementation follows the d365fo-client development guidelines:
- Use existing client functionality where possible
- Follow the MCP specification closely
- Add comprehensive tests for new features
- Update documentation for changes

See the main project README for detailed contribution guidelines.