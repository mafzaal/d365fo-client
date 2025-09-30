# FastMCP Migration Specification for d365fo-client

## Executive Summary

This specification outlines the migration of the d365fo-client MCP server from the traditional MCP SDK to FastMCP, enabling support for multiple transports (stdio, SSE, streamable-HTTP) and improved performance, scalability, and deployment flexibility.

## Current State Analysis

### Current Architecture Limitations
- **Single Transport**: Only stdio transport supported
- **Manual Routing**: Large if/elif chain for tool execution routing
- **No Web Support**: Cannot be deployed as a web service
- **Limited Scalability**: No built-in connection pooling or session management
- **Complex Setup**: Manual handler registration with decorators

### Current Capabilities (To Preserve)
- **29 Tools** across 7 categories (Connection, CRUD, Metadata, Labels, Profiles, Database, Sync)
- **5 Resource Handlers** (Entity, Environment, Metadata, Query, Database)
- **2 Prompts** (Sequence Analysis, Action Execution)
- **Full D365FO Integration** with authentication, caching, and error handling

## FastMCP Migration Architecture

### Core Design Principles
1. **Backward Compatibility**: All existing functionality preserved
2. **Enhanced Capabilities**: Multiple transports, web deployment, performance optimization
3. **Simplified Implementation**: Decorator-based approach reduces boilerplate
4. **Type Safety**: Enhanced type checking and validation
5. **Production Ready**: Built-in features for enterprise deployment

### New Server Architecture

```python
from mcp.server.fastmcp import FastMCP
from d365fo_client.mcp.client_manager import D365FOClientManager

class FastD365FOMCPServer:
    """FastMCP-based D365FO MCP Server with multi-transport support."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._load_default_config()
        self.client_manager = D365FOClientManager(self.config, self.profile_manager)
        
        # Initialize FastMCP server
        self.mcp = FastMCP(
            name="d365fo-mcp-server",
            instructions="Microsoft Dynamics 365 Finance & Operations MCP Server",
            host=self.config.get("host", "127.0.0.1"),
            port=self.config.get("port", 8000),
            debug=self.config.get("debug", False),
            json_response=self.config.get("json_response", False),
            stateless_http=self.config.get("stateless_http", False)
        )
        
        self._register_tools()
        self._register_resources()
        self._register_prompts()
    
    def run(self, transport: Literal["stdio", "sse", "streamable-http"] = "stdio"):
        """Run server with specified transport."""
        self.mcp.run(transport=transport)
```

## Transport Support Implementation

### 1. Stdio Transport (Default - Backward Compatibility)
```python
# Usage: d365fo-mcp-server
# or: d365fo-mcp-server --transport stdio
```
- **Use Case**: Development, command-line tools, VS Code integration
- **Benefits**: Low latency, simple setup, existing client compatibility
- **Configuration**: No additional setup required

### 2. SSE Transport (Server-Sent Events)
```python
# Usage: d365fo-mcp-server --transport sse --port 8000
```
- **Use Case**: Web applications, browser-based tools, real-time integrations
- **Benefits**: Web-compatible, real-time streaming, standardized
- **Configuration**: Port, CORS settings, authentication headers

### 3. Streamable HTTP Transport (Production)
```python
# Usage: d365fo-mcp-server --transport http --port 8000 --host 0.0.0.0
```
- **Use Case**: Production deployments, cloud services, microservices
- **Benefits**: Scalable, stateless options, load balancer compatible
- **Configuration**: Host, port, CORS, authentication, session management

## Tool Migration to FastMCP Decorators

### Before (Current Implementation)
```python
class ConnectionTools:
    def get_tools(self) -> List[Tool]:
        return [
            Tool(
                name="d365fo_test_connection",
                description="Test connection to D365FO environment",
                inputSchema={
                    "type": "object",
                    "properties": {"profile": {"type": "string"}},
                    "required": []
                }
            )
        ]
    
    async def execute_test_connection(self, arguments: dict) -> list[TextContent]:
        # Implementation
        pass
```

### After (FastMCP Implementation)
```python
@mcp.tool()
async def d365fo_test_connection(profile: str = None) -> str:
    """Test connection to D365FO environment.
    
    Args:
        profile: Optional profile name to test (uses default if not specified)
        
    Returns:
        Connection test result with status and details
    """
    client_manager = get_client_manager()  # Dependency injection
    result = await client_manager.test_connection(profile)
    return json.dumps(result, indent=2)
```

### Migration Benefits
- **50% Less Code**: Eliminates tool class boilerplate
- **Type Safety**: Automatic schema generation from function signatures
- **Error Handling**: Built-in exception handling and formatting
- **Documentation**: Docstrings become tool descriptions automatically

## Resource Migration to FastMCP

### Before (Current Implementation)
```python
class EntityResourceHandler:
    async def list_resources(self) -> List[Resource]:
        # Manual resource creation
        pass
    
    async def read_resource(self, uri: str) -> str:
        # Manual URI parsing and routing
        pass
```

### After (FastMCP Implementation)
```python
@mcp.resource("d365fo://entities/{entity_name}")
async def entity_resource(entity_name: str) -> str:
    """Get entity metadata and sample data.
    
    Args:
        entity_name: Name of the D365FO entity
        
    Returns:
        JSON containing entity schema and sample records
    """
    client_manager = get_client_manager()
    client = await client_manager.get_client()
    
    # Get entity schema
    schema = await client.get_entity_schema(entity_name)
    
    # Get sample data
    sample_data = await client.get_entities(entity_name, options=QueryOptions(top=5))
    
    return json.dumps({
        "schema": schema,
        "sample_data": sample_data,
        "entity_name": entity_name
    }, indent=2)
```

## Prompt Migration to FastMCP

### Before (Current Implementation)
```python
AVAILABLE_PROMPTS = {
    "d365fo_sequence_analysis": {
        "description": "Comprehensive analysis of D365 F&O sequence numbers",
        "template": "...",
        "arguments": SequenceAnalysisPromptArgs
    }
}
```

### After (FastMCP Implementation)
```python
@mcp.prompt()
async def d365fo_sequence_analysis(
    analysis_type: str = "comprehensive",
    scope: str = "company",
    entity_filter: str = None
) -> str:
    """Comprehensive analysis of D365 Finance & Operations sequence numbers.
    
    Args:
        analysis_type: Type of analysis (manual_sequences, entity_references, configuration_review, usage_patterns, comprehensive)
        scope: Analysis scope (company, legal_entity, operating_unit, global, all)
        entity_filter: Optional filter for specific entities
        
    Returns:
        Detailed analysis prompt for D365FO sequence number investigation
    """
    template = """
    # D365 Finance & Operations Sequence Number Analysis
    
    Please perform a {analysis_type} analysis of sequence numbers with scope: {scope}
    ...
    """
    
    return template.format(
        analysis_type=analysis_type,
        scope=scope,
        entity_filter=entity_filter or "all entities"
    )
```

## Configuration Enhancements

### New Configuration Structure
```python
{
    "server": {
        "name": "d365fo-mcp-server",
        "version": __version__,
        "transport": {
            "default": "stdio",
            "stdio": {
                "enabled": True
            },
            "sse": {
                "enabled": True,
                "host": "127.0.0.1",
                "port": 8000,
                "cors": {
                    "enabled": True,
                    "origins": ["*"],
                    "methods": ["GET", "POST"],
                    "headers": ["*"]
                }
            },
            "http": {
                "enabled": True,
                "host": "127.0.0.1", 
                "port": 8000,
                "stateless": False,
                "json_response": False,
                "cors": {
                    "enabled": True,
                    "origins": ["*"],
                    "methods": ["GET", "POST", "DELETE"],
                    "headers": ["*"]
                }
            }
        }
    },
    "d365fo": {
        # Existing D365FO configuration
    }
}
```

### CLI Enhancements
```bash
# Current
d365fo-mcp-server

# New options
d365fo-mcp-server --transport stdio                          # Default
d365fo-mcp-server --transport sse --port 8000               # SSE on port 8000
d365fo-mcp-server --transport http --port 8000 --host 0.0.0.0  # HTTP production
d365fo-mcp-server --transport http --stateless --json       # Stateless HTTP with JSON
```

## Performance and Scalability Improvements

### 1. Connection Pooling
```python
class FastD365FOMCPServer:
    def __init__(self, config):
        self.mcp = FastMCP(
            # Built-in session management
            stateless_http=config.get("stateless_http", False),
            # Performance optimizations
            debug=config.get("debug", False)
        )
```

### 2. Stateless HTTP Mode
- **Session Management**: Optional stateless operation for cloud deployment
- **Load Balancing**: Multiple server instances behind load balancer
- **Caching**: Shared cache across instances

### 3. JSON Response Mode
- **Client Compatibility**: Support for clients that prefer JSON over SSE
- **Performance**: Reduced overhead for simple request/response patterns

## Security Enhancements

### 1. CORS Configuration
```python
# Production CORS settings
cors_config = {
    "origins": ["https://yourdomain.com"],
    "methods": ["GET", "POST"],
    "headers": ["Authorization", "Content-Type", "Mcp-Session-Id"]
}
```

### 2. Authentication Integration
```python
# Future enhancement: OAuth/JWT support
@mcp.tool()
@require_auth(scopes=["d365fo:read"])
async def d365fo_query_entities(...):
    pass
```

## Deployment Strategies

### 1. Development Deployment
```bash
# Local development
d365fo-mcp-server --transport stdio

# Web testing
d365fo-mcp-server --transport sse --port 8000 --debug
```

### 2. Production Deployment
```bash
# Docker container
docker run -p 8000:8000 d365fo-mcp-server --transport http --host 0.0.0.0 --port 8000

# Kubernetes deployment
kubectl apply -f d365fo-mcp-server-deployment.yaml
```

### 3. Cloud Integration
```yaml
# Azure Container Apps
apiVersion: apps/v1
kind: Deployment
metadata:
  name: d365fo-mcp-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: d365fo-mcp-server
  template:
    spec:
      containers:
      - name: d365fo-mcp-server
        image: d365fo-mcp-server:latest
        args: ["--transport", "http", "--stateless", "--port", "8000"]
        env:
        - name: D365FO_BASE_URL
          valueFrom:
            secretKeyRef:
              name: d365fo-config
              key: base-url
```

## Testing Strategy

### 1. Unit Tests
```python
@pytest.mark.asyncio
async def test_fastmcp_tool_execution():
    """Test FastMCP tool execution."""
    server = FastD365FOMCPServer()
    
    # Test tool execution
    result = await server.d365fo_test_connection()
    assert "status" in result
```

### 2. Integration Tests
```python
@pytest.mark.asyncio
@pytest.mark.parametrize("transport", ["stdio", "sse", "http"])
async def test_transport_compatibility(transport):
    """Test all transports work correctly."""
    server = FastD365FOMCPServer()
    # Test transport-specific functionality
```

### 3. Performance Tests
```python
@pytest.mark.asyncio
async def test_concurrent_requests():
    """Test server performance under load."""
    # Concurrent request testing
```

## Migration Timeline

### Phase 1: Core FastMCP Implementation (Week 1)
1. Create new `FastD365FOMCPServer` class
2. Migrate 5 core tools (connection, basic CRUD)
3. Implement stdio transport compatibility
4. Basic testing

### Phase 2: Complete Tool Migration (Week 2)
1. Migrate all 29 tools to FastMCP decorators
2. Migrate all 5 resource handlers
3. Migrate 2 prompts
4. Comprehensive testing

### Phase 3: Transport Implementation (Week 3)
1. Implement SSE transport support
2. Implement HTTP transport support
3. Add CLI options for transport selection
4. CORS and security configuration

### Phase 4: Production Features (Week 4)
1. Stateless HTTP mode
2. JSON response support
3. Performance optimizations
4. Documentation and deployment guides

## Backward Compatibility

### Client Compatibility
- **Existing Clients**: Continue to work with stdio transport
- **Tool Names**: All tool names remain identical
- **Response Formats**: All response structures preserved
- **Configuration**: Existing environment variables supported

### Migration Path
1. **Gradual Migration**: New FastMCP server runs alongside current server
2. **Feature Parity**: All existing functionality preserved
3. **Default Behavior**: stdio transport remains default
4. **Configuration**: Existing configurations continue to work

## Benefits Summary

### Developer Experience
- **50% Less Code**: Decorator-based approach eliminates boilerplate
- **Better Debugging**: Built-in error handling and logging
- **Type Safety**: Automatic schema generation and validation
- **Simpler Deployment**: Multiple transport options

### Performance
- **Built-in Optimizations**: Connection pooling, session management
- **Scalability**: HTTP transport with load balancing support
- **Reduced Latency**: Optimized message handling

### Production Readiness
- **Web Deployment**: SSE and HTTP transports for cloud deployment
- **Security**: CORS support, authentication integration ready
- **Monitoring**: Better observability and health checks
- **Scalability**: Stateless mode for horizontal scaling

## Risk Mitigation

### Compatibility Risks
- **Mitigation**: Comprehensive testing with existing clients
- **Fallback**: Keep current implementation as backup
- **Validation**: Side-by-side testing during migration

### Performance Risks
- **Mitigation**: Performance testing with realistic workloads
- **Monitoring**: Built-in metrics and health checks
- **Optimization**: Profile and optimize critical paths

### Security Risks
- **Mitigation**: Security review of new transport implementations
- **Best Practices**: Follow FastMCP security guidelines
- **Testing**: Security testing of web transports

## Success Criteria

1. **Functional Compatibility**: All existing tools, resources, and prompts work identically
2. **Performance**: No regression in stdio transport performance
3. **New Capabilities**: SSE and HTTP transports work correctly
4. **Documentation**: Complete migration and deployment documentation
5. **Testing**: 95%+ test coverage for all components
6. **Production Ready**: Successful deployment in test environment

## Conclusion

The migration to FastMCP will significantly enhance the d365fo-client MCP server capabilities while maintaining full backward compatibility. The new architecture provides:

- **Multiple transport options** for different deployment scenarios
- **Simplified implementation** with decorator-based approach
- **Enhanced performance** with built-in optimizations
- **Production readiness** with web server capabilities
- **Better developer experience** with reduced boilerplate

This migration positions the d365fo-client MCP server as a enterprise-ready solution suitable for development, testing, and production deployments across various environments and use cases.