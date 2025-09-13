# MCP Server to Server-Sent Events (SSE) Conversion Analysis

## Overview

This document analyzes the current Model Context Protocol (MCP) server implementation and provides a comprehensive plan for converting it to use Server-Sent Events (SSE) as the transport mechanism instead of the current stdio-based approach.

## Current MCP Implementation Architecture

### Core Components

```
D365FOMCPServer (current)
├── Transport Layer: stdio (mcp.server.stdio.stdio_server)
├── Protocol Handler: MCP 1.13.0 compliant
├── Resource Handlers: 4 types
│   ├── EntityResourceHandler
│   ├── MetadataResourceHandler  
│   ├── EnvironmentResourceHandler
│   ├── QueryResourceHandler
│   └── DatabaseResourceHandler
├── Tool Handlers: 12 tools
│   ├── Connection Tools (2)
│   ├── CRUD Tools (6)
│   ├── Metadata Tools (6)
│   ├── Label Tools (2)
│   ├── Profile Tools (8)
│   ├── Database Tools (4)
│   └── Sync Tools (5)
└── Client Manager: Connection pooling
```

### Current Transport Implementation

**File**: `src/d365fo_client/mcp/server.py:338-367`

```python
async def run(self, transport_type: str = "stdio"):
    """Run the MCP server."""
    if transport_type == "stdio":
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(...)
            )
    else:
        raise ValueError(f"Unsupported transport type: {transport_type}")
```

**Key Points**:
- Transport is abstracted via `transport_type` parameter
- Currently only supports "stdio" 
- Uses MCP library's `stdio_server()` context manager
- Ready for extension to other transport types

## Server-Sent Events (SSE) Overview

### What is SSE?

Server-Sent Events (SSE) is a web standard that allows a server to push data to a web page over a single HTTP connection. Unlike WebSockets, SSE is unidirectional (server-to-client) and uses standard HTTP.

### SSE Characteristics

- **Protocol**: HTTP-based with `text/event-stream` content type
- **Direction**: Unidirectional (server → client)
- **Connection**: Long-lived HTTP connection
- **Format**: Text-based with specific event format
- **Reconnection**: Built-in automatic reconnection

### SSE Event Format

```
event: message_type
data: {"key": "value"}
id: unique_event_id
retry: 3000

```

## Why Convert MCP to SSE?

### Benefits of SSE over stdio

1. **Web Compatibility**: Direct browser/web app integration
2. **HTTP-based**: Works with existing web infrastructure  
3. **Real-time Updates**: Push notifications and live data
4. **Firewall Friendly**: Uses standard HTTP ports
5. **Streaming**: Continuous data flow for large datasets
6. **Reconnection**: Built-in resilience
7. **Scalability**: HTTP load balancing and caching

### Use Cases Enabled by SSE

1. **Web Dashboard**: Real-time D365FO monitoring dashboards
2. **Live Data Streams**: Continuous entity updates
3. **Progress Tracking**: Real-time sync/import progress
4. **Notifications**: System alerts and status changes
5. **Multi-client**: Multiple web clients consuming same data
6. **Integration Monitoring**: Live API call tracking

## SSE Conversion Architecture

### Proposed Architecture

```
D365FOSSEServer (proposed)
├── Transport Layer: SSE (aiohttp-based)
├── HTTP Server: aiohttp web server
├── SSE Endpoints:
│   ├── /sse/events - Main event stream
│   ├── /sse/tools/{tool_name} - Tool-specific streams
│   ├── /sse/resources/{resource_type} - Resource streams
│   └── /sse/status - Server status stream
├── Protocol Adaptation: MCP-to-SSE message conversion
├── Resource Handlers: Same 4 types (reused)
├── Tool Handlers: Same 12 tools (reused)
└── Client Manager: Same connection pooling (reused)
```

### SSE Event Types

#### Core MCP Events
- `mcp_tool_call` - Tool execution requests
- `mcp_tool_response` - Tool execution results  
- `mcp_resource_request` - Resource access requests
- `mcp_resource_response` - Resource data responses
- `mcp_prompt_request` - Prompt requests
- `mcp_prompt_response` - Prompt responses

#### D365FO-Specific Events
- `d365fo_entity_update` - Real-time entity changes
- `d365fo_sync_progress` - Metadata sync progress
- `d365fo_connection_status` - Connection health updates
- `d365fo_error` - Error notifications
- `d365fo_metrics` - Performance metrics

## Implementation Plan

### Phase 1: Core SSE Infrastructure

#### 1.1 Add Dependencies

**File**: `pyproject.toml`

```toml
dependencies = [
    # ... existing dependencies ...
    "aiohttp>=3.10.0",  # Already present
    "aiohttp-sse>=0.2.0",  # New - SSE support
]
```

#### 1.2 Create SSE Server Base

**File**: `src/d365fo_client/sse/__init__.py` (new)

```python
"""Server-Sent Events implementation for d365fo-client."""

from .server import D365FOSSEServer
from .events import SSEEventManager
from .transport import SSETransport

__all__ = [
    "D365FOSSEServer",
    "SSEEventManager", 
    "SSETransport",
]
```

#### 1.3 SSE Transport Implementation

**File**: `src/d365fo_client/sse/transport.py` (new)

```python
"""SSE transport implementation for MCP protocol."""

import asyncio
import json
import logging
from typing import Any, AsyncIterator, Dict, Optional
from aiohttp import web
from aiohttp_sse import sse_response

logger = logging.getLogger(__name__)

class SSETransport:
    """SSE transport for MCP protocol messages."""
    
    def __init__(self):
        self.clients: Dict[str, web.StreamResponse] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
    
    async def add_client(self, client_id: str, response: web.StreamResponse):
        """Add SSE client connection."""
        self.clients[client_id] = response
        logger.info(f"SSE client connected: {client_id}")
    
    async def remove_client(self, client_id: str):
        """Remove SSE client connection."""
        if client_id in self.clients:
            del self.clients[client_id]
            logger.info(f"SSE client disconnected: {client_id}")
    
    async def broadcast_event(self, event_type: str, data: Dict[str, Any]):
        """Broadcast event to all connected clients."""
        event_data = json.dumps(data)
        
        disconnected_clients = []
        for client_id, response in self.clients.items():
            try:
                await response.send_data(
                    event_data,
                    event=event_type
                )
            except Exception as e:
                logger.warning(f"Failed to send to client {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.remove_client(client_id)
```

#### 1.4 SSE Event Manager

**File**: `src/d365fo_client/sse/events.py` (new)

```python
"""SSE event management for MCP protocol."""

import json
import logging
from typing import Any, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class SSEEventType(Enum):
    """SSE event types for MCP protocol."""
    
    # Core MCP events
    MCP_TOOL_CALL = "mcp_tool_call"
    MCP_TOOL_RESPONSE = "mcp_tool_response"
    MCP_RESOURCE_REQUEST = "mcp_resource_request"
    MCP_RESOURCE_RESPONSE = "mcp_resource_response"
    MCP_PROMPT_REQUEST = "mcp_prompt_request"
    MCP_PROMPT_RESPONSE = "mcp_prompt_response"
    
    # D365FO-specific events
    D365FO_ENTITY_UPDATE = "d365fo_entity_update"
    D365FO_SYNC_PROGRESS = "d365fo_sync_progress"
    D365FO_CONNECTION_STATUS = "d365fo_connection_status"
    D365FO_ERROR = "d365fo_error"
    D365FO_METRICS = "d365fo_metrics"
    
    # Server events
    SERVER_CONNECTED = "server_connected"
    SERVER_DISCONNECTED = "server_disconnected"
    SERVER_STATUS = "server_status"

class SSEEventManager:
    """Manages SSE events and formatting."""
    
    def __init__(self, transport):
        self.transport = transport
    
    async def send_tool_call(self, tool_name: str, arguments: Dict[str, Any], request_id: str):
        """Send tool call event."""
        await self.transport.broadcast_event(
            SSEEventType.MCP_TOOL_CALL.value,
            {
                "request_id": request_id,
                "tool_name": tool_name,
                "arguments": arguments,
                "timestamp": self._get_timestamp()
            }
        )
    
    async def send_tool_response(self, tool_name: str, result: Any, request_id: str):
        """Send tool response event."""
        await self.transport.broadcast_event(
            SSEEventType.MCP_TOOL_RESPONSE.value,
            {
                "request_id": request_id,
                "tool_name": tool_name,
                "result": result,
                "timestamp": self._get_timestamp()
            }
        )
    
    async def send_resource_data(self, resource_uri: str, data: str):
        """Send resource data event."""
        await self.transport.broadcast_event(
            SSEEventType.MCP_RESOURCE_RESPONSE.value,
            {
                "resource_uri": resource_uri,
                "data": data,
                "timestamp": self._get_timestamp()
            }
        )
    
    async def send_sync_progress(self, operation: str, progress: Dict[str, Any]):
        """Send sync progress event."""
        await self.transport.broadcast_event(
            SSEEventType.D365FO_SYNC_PROGRESS.value,
            {
                "operation": operation,
                "progress": progress,
                "timestamp": self._get_timestamp()
            }
        )
    
    async def send_error(self, error_type: str, message: str, context: Optional[Dict[str, Any]] = None):
        """Send error event."""
        await self.transport.broadcast_event(
            SSEEventType.D365FO_ERROR.value,
            {
                "error_type": error_type,
                "message": message,
                "context": context or {},
                "timestamp": self._get_timestamp()
            }
        )
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat()
```

### Phase 2: SSE Server Implementation

#### 2.1 Main SSE Server

**File**: `src/d365fo_client/sse/server.py` (new)

```python
"""SSE Server implementation for d365fo-client."""

import asyncio
import logging
import uuid
from typing import Any, Dict, Optional
from aiohttp import web, ClientSession
from aiohttp_sse import sse_response

from ..mcp.server import D365FOMCPServer
from .transport import SSETransport
from .events import SSEEventManager, SSEEventType

logger = logging.getLogger(__name__)

class D365FOSSEServer(D365FOMCPServer):
    """SSE Server for Microsoft Dynamics 365 Finance & Operations.
    
    Extends the MCP server to support Server-Sent Events transport.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, port: int = 8080):
        """Initialize the SSE server.
        
        Args:
            config: Configuration dictionary
            port: HTTP server port
        """
        super().__init__(config)
        self.port = port
        self.app = web.Application()
        self.transport = SSETransport()
        self.event_manager = SSEEventManager(self.transport)
        
        # Setup HTTP routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup HTTP routes for SSE endpoints."""
        self.app.router.add_get('/sse/events', self.handle_sse_events)
        self.app.router.add_get('/sse/status', self.handle_sse_status)
        self.app.router.add_post('/api/tools/{tool_name}', self.handle_tool_call)
        self.app.router.add_get('/api/resources/{resource_type}', self.handle_resource_request)
        self.app.router.add_get('/health', self.handle_health)
        
        # CORS support
        self.app.router.add_options('/{path:.*}', self.handle_options)
    
    async def handle_sse_events(self, request: web.Request) -> web.StreamResponse:
        """Handle main SSE event stream."""
        client_id = str(uuid.uuid4())
        
        async with sse_response(request) as resp:
            await self.transport.add_client(client_id, resp)
            
            # Send welcome message
            await resp.send_data(
                '{"message": "Connected to D365FO SSE Server"}',
                event=SSEEventType.SERVER_CONNECTED.value
            )
            
            try:
                # Keep connection alive
                while not resp.task.done():
                    await asyncio.sleep(1)
            finally:
                await self.transport.remove_client(client_id)
        
        return resp
    
    async def handle_sse_status(self, request: web.Request) -> web.StreamResponse:
        """Handle server status SSE stream."""
        async with sse_response(request) as resp:
            while not resp.task.done():
                status = await self._get_server_status()
                await resp.send_data(
                    json.dumps(status),
                    event=SSEEventType.SERVER_STATUS.value
                )
                await asyncio.sleep(5)  # Send status every 5 seconds
        
        return resp
    
    async def handle_tool_call(self, request: web.Request) -> web.Response:
        """Handle HTTP tool call requests."""
        tool_name = request.match_info['tool_name']
        request_id = str(uuid.uuid4())
        
        try:
            # Parse request body
            if request.content_type == 'application/json':
                arguments = await request.json()
            else:
                arguments = {}
            
            # Send tool call event
            await self.event_manager.send_tool_call(tool_name, arguments, request_id)
            
            # Execute tool (reuse existing MCP tool execution)
            result = await self._execute_tool(tool_name, arguments)
            
            # Send tool response event
            await self.event_manager.send_tool_response(tool_name, result, request_id)
            
            return web.json_response({
                "request_id": request_id,
                "tool_name": tool_name,
                "result": result
            })
            
        except Exception as e:
            await self.event_manager.send_error("tool_execution", str(e), {
                "tool_name": tool_name,
                "request_id": request_id
            })
            return web.json_response({
                "error": str(e),
                "tool_name": tool_name,
                "request_id": request_id
            }, status=500)
    
    async def handle_resource_request(self, request: web.Request) -> web.Response:
        """Handle HTTP resource requests."""
        resource_type = request.match_info['resource_type']
        resource_id = request.query.get('id', '')
        
        try:
            # Build resource URI
            resource_uri = f"d365fo://{resource_type}/{resource_id}"
            
            # Get resource data (reuse existing MCP resource handlers)
            data = await self._get_resource_data(resource_uri)
            
            # Send resource data event
            await self.event_manager.send_resource_data(resource_uri, data)
            
            return web.Response(text=data, content_type='application/json')
            
        except Exception as e:
            await self.event_manager.send_error("resource_access", str(e), {
                "resource_type": resource_type,
                "resource_id": resource_id
            })
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_health(self, request: web.Request) -> web.Response:
        """Handle health check requests."""
        status = await self._get_server_status()
        return web.json_response(status)
    
    async def handle_options(self, request: web.Request) -> web.Response:
        """Handle CORS preflight requests."""
        return web.Response(
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            }
        )
    
    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """Execute tool using existing MCP infrastructure."""
        # This reuses the existing tool execution logic from the parent MCP server
        # We can call the existing handle_call_tool method
        text_results = await super().handle_call_tool(tool_name, arguments)
        
        # Convert TextContent results to JSON-serializable format
        results = []
        for result in text_results:
            if hasattr(result, 'text'):
                try:
                    # Try to parse as JSON
                    import json
                    results.append(json.loads(result.text))
                except json.JSONDecodeError:
                    # If not JSON, return as text
                    results.append({"text": result.text})
            else:
                results.append(str(result))
        
        return results[0] if len(results) == 1 else results
    
    async def _get_resource_data(self, resource_uri: str) -> str:
        """Get resource data using existing MCP infrastructure."""
        # This reuses the existing resource handling logic
        return await super().handle_read_resource(resource_uri)
    
    async def _get_server_status(self) -> Dict[str, Any]:
        """Get current server status."""
        return {
            "server": "d365fo-sse-server",
            "version": self.__version__,
            "connected_clients": len(self.transport.clients),
            "uptime": "TODO",  # Implement uptime tracking
            "memory_usage": "TODO",  # Implement memory tracking
        }
    
    async def run_sse(self):
        """Run the SSE server."""
        try:
            logger.info(f"Starting D365FO SSE Server on port {self.port}...")
            
            # Perform startup initialization
            await self._startup_initialization()
            
            # Start HTTP server
            runner = web.AppRunner(self.app)
            await runner.setup()
            
            site = web.TCPSite(runner, '0.0.0.0', self.port)
            await site.start()
            
            logger.info(f"D365FO SSE Server running on http://0.0.0.0:{self.port}")
            logger.info("SSE endpoints:")
            logger.info(f"  - Events: http://0.0.0.0:{self.port}/sse/events")
            logger.info(f"  - Status: http://0.0.0.0:{self.port}/sse/status")
            logger.info(f"  - Health: http://0.0.0.0:{self.port}/health")
            
            # Keep server running
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error running SSE server: {e}")
            raise
        finally:
            await self.cleanup()
```

### Phase 3: Entry Point and Configuration

#### 3.1 SSE Entry Point

**File**: `src/d365fo_client/sse/main.py` (new)

```python
#!/usr/bin/env python3
"""Entry point for the D365FO SSE Server."""

import asyncio
import logging
import os
import sys
from pathlib import Path

from d365fo_client import __version__
from d365fo_client.sse import D365FOSSEServer

def setup_logging(level: str = "INFO") -> None:
    """Set up logging for the SSE server."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create logs directory
    log_dir = Path.home() / ".d365fo-sse" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "sse-server.log"),
            logging.StreamHandler(sys.stderr),
        ],
        force=True,
    )

def load_config():
    """Load configuration from environment variables."""
    # Reuse the same configuration logic as MCP server
    from d365fo_client.mcp.main import load_config
    return load_config()

async def async_main() -> None:
    """Async main entry point for the SSE server."""
    try:
        # Set up logging
        log_level = os.getenv("D365FO_LOG_LEVEL", "INFO")
        setup_logging(log_level)
        
        # Get port from environment
        port = int(os.getenv("D365FO_SSE_PORT", "8080"))
        
        logging.info(f"D365FO SSE Server v{__version__}")
        
        # Load configuration
        config = load_config()
        
        # Create and run SSE server
        server = D365FOSSEServer(config, port)
        await server.run_sse()
        
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
    except Exception as e:
        logging.error(f"Server error: {e}")
        sys.exit(1)

def main() -> None:
    """Main entry point for the SSE server."""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
```

#### 3.2 Update Project Configuration

**File**: `pyproject.toml` (modify)

```toml
[project.scripts]
d365fo-client = "d365fo_client.main:main"
d365fo-mcp-server = "d365fo_client.mcp.main:main"
d365fo-sse-server = "d365fo_client.sse.main:main"  # New entry point

[project]
dependencies = [
    # ... existing dependencies ...
    "aiohttp-sse>=0.2.0",  # Add SSE support
]
```

## Implementation Benefits

### 1. **Web Integration**
- Direct browser/JavaScript integration
- No special client libraries required
- Works with existing web frameworks

### 2. **Real-Time Capabilities**
- Live D365FO data streams
- Real-time sync progress updates
- Instant error notifications

### 3. **Scalability**
- HTTP load balancing
- Multiple client support
- Standard web infrastructure

### 4. **Development Experience**
- Web-based debugging tools
- Standard HTTP testing tools
- Browser developer console integration

### 5. **Monitoring & Observability**
- HTTP access logs
- Standard web metrics
- Load balancer integration

## Testing Strategy

### 1. **Unit Tests**
- SSE transport functionality
- Event formatting and serialization
- HTTP endpoint handlers

### 2. **Integration Tests**
- Full SSE server startup
- Client connection handling
- Tool execution via HTTP API
- Resource access via HTTP API

### 3. **Performance Tests**
- Multiple client connections
- High-frequency event streaming
- Large dataset transmission

### 4. **Browser Compatibility**
- JavaScript EventSource API
- Cross-browser testing
- CORS functionality

## Migration Path

### Phase 1: Infrastructure (Week 1)
- [ ] Add aiohttp-sse dependency
- [ ] Create SSE transport and event manager
- [ ] Implement basic SSE server structure

### Phase 2: Core Functionality (Week 2)  
- [ ] Implement tool execution via HTTP API
- [ ] Implement resource access via HTTP API
- [ ] Add SSE event streaming for all MCP operations

### Phase 3: Enhancement (Week 3)
- [ ] Add real-time D365FO event streaming
- [ ] Implement progress tracking for long operations
- [ ] Add monitoring and metrics endpoints

### Phase 4: Testing & Documentation (Week 4)
- [ ] Comprehensive testing suite
- [ ] Browser client examples
- [ ] Documentation and tutorials
- [ ] Performance optimization

## Usage Examples

### JavaScript Client Example

```javascript
// Connect to SSE server
const eventSource = new EventSource('http://localhost:8080/sse/events');

// Listen for tool responses
eventSource.addEventListener('mcp_tool_response', (event) => {
    const data = JSON.parse(event.data);
    console.log('Tool result:', data);
});

// Listen for sync progress
eventSource.addEventListener('d365fo_sync_progress', (event) => {
    const data = JSON.parse(event.data);
    updateProgressBar(data.progress);
});

// Execute tool via HTTP API
async function executeTool(toolName, arguments) {
    const response = await fetch(`http://localhost:8080/api/tools/${toolName}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(arguments)
    });
    return response.json();
}

// Get resource data
async function getResource(resourceType, resourceId) {
    const response = await fetch(`http://localhost:8080/api/resources/${resourceType}?id=${resourceId}`);
    return response.text();
}
```

### Python Client Example

```python
import aiohttp
import asyncio
import json

async def sse_client():
    """Example SSE client in Python."""
    session = aiohttp.ClientSession()
    
    try:
        # Connect to SSE stream
        async with session.get('http://localhost:8080/sse/events') as response:
            async for line in response.content:
                if line.startswith(b'data: '):
                    data = json.loads(line[6:].decode())
                    print(f"Received event: {data}")
                    
    finally:
        await session.close()

# Execute tool
async def execute_tool(tool_name, arguments):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f'http://localhost:8080/api/tools/{tool_name}',
            json=arguments
        ) as response:
            return await response.json()
```

## Conclusion

Converting the MCP server to use Server-Sent Events provides significant benefits for web integration, real-time capabilities, and scalability while maintaining all existing functionality. The implementation reuses the existing MCP infrastructure (tools, resources, client management) and adds a modern HTTP/SSE transport layer.

Key advantages:
- ✅ **Web-native**: Direct browser integration
- ✅ **Real-time**: Live data streaming capabilities  
- ✅ **Scalable**: Standard HTTP infrastructure
- ✅ **Compatible**: Maintains all existing MCP functionality
- ✅ **Extensible**: Easy to add new SSE event types

The proposed implementation provides a clear migration path while preserving the investment in the existing MCP server codebase.