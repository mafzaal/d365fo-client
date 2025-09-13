#!/usr/bin/env python3
"""Demonstration of MCP to SSE conversion concepts.

This example shows how the current MCP server could be converted to use
Server-Sent Events (SSE) instead of stdio transport.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from aiohttp import web
import aiohttp
from contextlib import asynccontextmanager

# This would normally import from aiohttp-sse, but for demo purposes we'll simulate
class MockSSEResponse:
    """Mock SSE response for demonstration."""
    
    def __init__(self):
        self.task = asyncio.create_task(asyncio.sleep(0))
        self.closed = False
    
    async def send_data(self, data: str, event: str = None):
        """Send SSE event data."""
        if self.closed:
            return
        
        event_line = f"event: {event}\n" if event else ""
        data_line = f"data: {data}\n"
        timestamp = datetime.utcnow().isoformat()
        id_line = f"id: {timestamp}\n"
        
        message = f"{event_line}{data_line}{id_line}\n"
        print(f"[SSE] Sending: {message.strip()}")

@asynccontextmanager
async def mock_sse_response(request):
    """Mock SSE response context manager."""
    response = MockSSEResponse()
    try:
        yield response
    finally:
        response.closed = True

class D365FOSSEDemo:
    """Demonstration of D365FO SSE Server implementation."""
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.app = web.Application()
        self.clients: Dict[str, MockSSEResponse] = {}
        self.setup_routes()
    
    def setup_routes(self):
        """Setup HTTP routes for SSE demo."""
        self.app.router.add_get('/sse/events', self.handle_sse_events)
        self.app.router.add_get('/sse/status', self.handle_sse_status)
        self.app.router.add_post('/api/tools/{tool_name}', self.handle_tool_call)
        self.app.router.add_get('/api/resources/{resource_type}', self.handle_resource_request)
        self.app.router.add_get('/health', self.handle_health)
        self.app.router.add_get('/', self.handle_index)
    
    async def handle_index(self, request: web.Request) -> web.Response:
        """Handle index page with JavaScript SSE client."""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>D365FO SSE Demo</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .event-log { 
            background: #f5f5f5; 
            padding: 10px; 
            height: 300px; 
            overflow-y: scroll; 
            margin: 10px 0; 
            border: 1px solid #ddd;
        }
        .event { margin: 5px 0; padding: 5px; background: white; border-left: 3px solid #007acc; }
        .tool-form { margin: 20px 0; padding: 15px; border: 1px solid #ddd; }
        .tool-form input, .tool-form button { margin: 5px; padding: 8px; }
        button { background: #007acc; color: white; border: none; cursor: pointer; }
        button:hover { background: #005999; }
    </style>
</head>
<body>
    <div class="container">
        <h1>D365FO Server-Sent Events Demo</h1>
        
        <div>
            <h2>Connection Status</h2>
            <div id="status">Connecting...</div>
        </div>
        
        <div>
            <h2>Event Stream</h2>
            <div id="eventLog" class="event-log"></div>
            <button onclick="clearLog()">Clear Log</button>
        </div>
        
        <div class="tool-form">
            <h2>Execute Tool</h2>
            <input type="text" id="toolName" placeholder="Tool name (e.g., d365fo_test_connection)" />
            <input type="text" id="toolArgs" placeholder="Arguments (JSON)" />
            <button onclick="executeTool()">Execute</button>
        </div>
        
        <div class="tool-form">
            <h2>Get Resource</h2>
            <input type="text" id="resourceType" placeholder="Resource type (e.g., entities)" />
            <input type="text" id="resourceId" placeholder="Resource ID (e.g., CustomersV3)" />
            <button onclick="getResource()">Get Resource</button>
        </div>
    </div>
    
    <script>
        let eventSource;
        let eventCount = 0;
        
        function log(message, type = 'info') {
            const logDiv = document.getElementById('eventLog');
            const eventDiv = document.createElement('div');
            eventDiv.className = 'event';
            eventDiv.innerHTML = `<strong>${new Date().toLocaleTimeString()}</strong> [${type}] ${message}`;
            logDiv.appendChild(eventDiv);
            logDiv.scrollTop = logDiv.scrollHeight;
            
            eventCount++;
            if (eventCount > 100) {
                // Keep only last 100 events
                logDiv.removeChild(logDiv.firstChild);
                eventCount--;
            }
        }
        
        function clearLog() {
            document.getElementById('eventLog').innerHTML = '';
            eventCount = 0;
        }
        
        function connectSSE() {
            eventSource = new EventSource('/sse/events');
            
            eventSource.onopen = function(event) {
                document.getElementById('status').innerHTML = 
                    '<span style="color: green;">✓ Connected to SSE stream</span>';
                log('Connected to D365FO SSE Server', 'success');
            };
            
            eventSource.onerror = function(event) {
                document.getElementById('status').innerHTML = 
                    '<span style="color: red;">✗ Connection error</span>';
                log('SSE connection error', 'error');
            };
            
            // Listen for all event types
            ['server_connected', 'mcp_tool_call', 'mcp_tool_response', 
             'mcp_resource_response', 'd365fo_sync_progress', 'd365fo_error',
             'server_status'].forEach(eventType => {
                eventSource.addEventListener(eventType, function(event) {
                    try {
                        const data = JSON.parse(event.data);
                        log(`<strong>${eventType}:</strong> ${JSON.stringify(data, null, 2)}`, eventType);
                    } catch (e) {
                        log(`<strong>${eventType}:</strong> ${event.data}`, eventType);
                    }
                });
            });
        }
        
        async function executeTool() {
            const toolName = document.getElementById('toolName').value;
            const toolArgsText = document.getElementById('toolArgs').value;
            
            if (!toolName) {
                alert('Please enter a tool name');
                return;
            }
            
            let arguments = {};
            if (toolArgsText) {
                try {
                    arguments = JSON.parse(toolArgsText);
                } catch (e) {
                    alert('Invalid JSON in arguments');
                    return;
                }
            }
            
            try {
                log(`Executing tool: ${toolName}`, 'request');
                
                const response = await fetch(`/api/tools/${toolName}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(arguments)
                });
                
                const result = await response.json();
                log(`Tool result: ${JSON.stringify(result, null, 2)}`, 'response');
                
            } catch (error) {
                log(`Tool execution error: ${error.message}`, 'error');
            }
        }
        
        async function getResource() {
            const resourceType = document.getElementById('resourceType').value;
            const resourceId = document.getElementById('resourceId').value;
            
            if (!resourceType) {
                alert('Please enter a resource type');
                return;
            }
            
            try {
                log(`Getting resource: ${resourceType}/${resourceId}`, 'request');
                
                const url = `/api/resources/${resourceType}${resourceId ? '?id=' + resourceId : ''}`;
                const response = await fetch(url);
                const result = await response.text();
                
                log(`Resource data: ${result}`, 'response');
                
            } catch (error) {
                log(`Resource fetch error: ${error.message}`, 'error');
            }
        }
        
        // Connect when page loads
        window.onload = connectSSE;
    </script>
</body>
</html>
        """
        return web.Response(text=html, content_type='text/html')
    
    async def handle_sse_events(self, request: web.Request) -> web.StreamResponse:
        """Handle main SSE event stream."""
        client_id = str(uuid.uuid4())
        
        # In real implementation, this would use aiohttp-sse
        async with mock_sse_response(request) as resp:
            self.clients[client_id] = resp
            
            # Send welcome message
            await resp.send_data(
                json.dumps({"message": "Connected to D365FO SSE Demo Server", "client_id": client_id}),
                event="server_connected"
            )
            
            try:
                # Keep connection alive
                while not resp.task.done():
                    await asyncio.sleep(1)
            finally:
                if client_id in self.clients:
                    del self.clients[client_id]
        
        return web.Response(text="SSE stream ended")
    
    async def handle_sse_status(self, request: web.Request) -> web.StreamResponse:
        """Handle server status SSE stream."""
        async with mock_sse_response(request) as resp:
            while not resp.task.done():
                status = {
                    "server": "d365fo-sse-demo",
                    "connected_clients": len(self.clients),
                    "timestamp": datetime.utcnow().isoformat(),
                    "uptime": "demo_mode"
                }
                await resp.send_data(
                    json.dumps(status),
                    event="server_status"
                )
                await asyncio.sleep(5)  # Send status every 5 seconds
        
        return web.Response(text="Status stream ended")
    
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
            
            # Broadcast tool call event to all SSE clients
            await self.broadcast_event("mcp_tool_call", {
                "request_id": request_id,
                "tool_name": tool_name,
                "arguments": arguments,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Simulate tool execution (in real implementation, this would call actual MCP tools)
            result = await self.simulate_tool_execution(tool_name, arguments)
            
            # Broadcast tool response event
            await self.broadcast_event("mcp_tool_response", {
                "request_id": request_id,
                "tool_name": tool_name,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return web.json_response({
                "request_id": request_id,
                "tool_name": tool_name,
                "result": result
            })
            
        except Exception as e:
            await self.broadcast_event("d365fo_error", {
                "error_type": "tool_execution",
                "message": str(e),
                "context": {
                    "tool_name": tool_name,
                    "request_id": request_id
                },
                "timestamp": datetime.utcnow().isoformat()
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
            
            # Simulate resource data retrieval
            data = await self.simulate_resource_data(resource_type, resource_id)
            
            # Broadcast resource data event
            await self.broadcast_event("mcp_resource_response", {
                "resource_uri": resource_uri,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return web.Response(text=json.dumps(data), content_type='application/json')
            
        except Exception as e:
            await self.broadcast_event("d365fo_error", {
                "error_type": "resource_access",
                "message": str(e),
                "context": {
                    "resource_type": resource_type,
                    "resource_id": resource_id
                },
                "timestamp": datetime.utcnow().isoformat()
            })
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_health(self, request: web.Request) -> web.Response:
        """Handle health check requests."""
        status = {
            "server": "d365fo-sse-demo",
            "version": "demo",
            "connected_clients": len(self.clients),
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }
        return web.json_response(status)
    
    async def broadcast_event(self, event_type: str, data: Dict[str, Any]):
        """Broadcast event to all connected SSE clients."""
        event_data = json.dumps(data)
        
        disconnected_clients = []
        for client_id, response in self.clients.items():
            try:
                await response.send_data(event_data, event=event_type)
            except Exception as e:
                print(f"Failed to send to client {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            if client_id in self.clients:
                del self.clients[client_id]
    
    async def simulate_tool_execution(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate D365FO tool execution."""
        # Simulate processing time
        await asyncio.sleep(0.5)
        
        if tool_name == "d365fo_test_connection":
            return {
                "status": "success",
                "connection": "healthy",
                "response_time_ms": 150,
                "environment": "demo-environment"
            }
        elif tool_name == "d365fo_query_entities":
            return {
                "entities": [
                    {"name": "CustomersV3", "count": 1250},
                    {"name": "VendorsV2", "count": 850},
                    {"name": "ItemsV3", "count": 3200}
                ],
                "total_count": 3
            }
        elif tool_name == "d365fo_search_entities":
            pattern = arguments.get("pattern", "")
            return {
                "pattern": pattern,
                "results": [
                    {"name": f"Entity{i}", "label": f"Test Entity {i}", "category": "Master"}
                    for i in range(1, 6)
                ],
                "count": 5
            }
        else:
            return {
                "tool_name": tool_name,
                "arguments": arguments,
                "result": "Tool execution simulated",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def simulate_resource_data(self, resource_type: str, resource_id: str) -> Dict[str, Any]:
        """Simulate D365FO resource data retrieval."""
        # Simulate processing time
        await asyncio.sleep(0.3)
        
        if resource_type == "entities":
            if resource_id:
                return {
                    "name": resource_id,
                    "label": f"Label for {resource_id}",
                    "properties": [
                        {"name": "Id", "type": "String", "is_key": True},
                        {"name": "Name", "type": "String", "is_key": False},
                        {"name": "Status", "type": "Enum", "is_key": False}
                    ],
                    "sample_data": [
                        {"Id": "001", "Name": "Sample Entity 1", "Status": "Active"},
                        {"Id": "002", "Name": "Sample Entity 2", "Status": "Inactive"}
                    ]
                }
            else:
                return {
                    "entities": [
                        {"name": "CustomersV3", "label": "Customers"},
                        {"name": "VendorsV2", "label": "Vendors"},
                        {"name": "ItemsV3", "label": "Items"}
                    ],
                    "count": 3
                }
        elif resource_type == "metadata":
            return {
                "type": "metadata",
                "environment": "demo-environment",
                "version": "10.0.40",
                "last_updated": datetime.utcnow().isoformat()
            }
        else:
            return {
                "resource_type": resource_type,
                "resource_id": resource_id,
                "data": "Simulated resource data",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def run_demo(self):
        """Run the SSE demo server."""
        try:
            print(f"Starting D365FO SSE Demo Server on port {self.port}...")
            print(f"Open http://localhost:{self.port} in your browser to see the demo")
            print("Available endpoints:")
            print(f"  - Demo UI: http://localhost:{self.port}")
            print(f"  - Events: http://localhost:{self.port}/sse/events")
            print(f"  - Status: http://localhost:{self.port}/sse/status")
            print(f"  - Health: http://localhost:{self.port}/health")
            print("\nPress Ctrl+C to stop the server")
            
            runner = web.AppRunner(self.app)
            await runner.setup()
            
            site = web.TCPSite(runner, '0.0.0.0', self.port)
            await site.start()
            
            # Start background task to simulate periodic events
            asyncio.create_task(self.simulate_periodic_events())
            
            # Keep server running
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("\nShutting down SSE demo server...")
        except Exception as e:
            print(f"Error running SSE demo server: {e}")
            raise
    
    async def simulate_periodic_events(self):
        """Simulate periodic D365FO events."""
        while True:
            await asyncio.sleep(10)  # Every 10 seconds
            
            # Simulate sync progress event
            await self.broadcast_event("d365fo_sync_progress", {
                "operation": "metadata_sync",
                "progress": {
                    "percentage": (datetime.now().second % 100),
                    "current_entity": f"Entity_{datetime.now().second}",
                    "total_entities": 100
                },
                "timestamp": datetime.utcnow().isoformat()
            })

async def main():
    """Main entry point for the SSE demo."""
    import argparse
    
    parser = argparse.ArgumentParser(description="D365FO SSE Conversion Demo")
    parser.add_argument("--port", type=int, default=8080, help="HTTP server port")
    args = parser.parse_args()
    
    demo = D365FOSSEDemo(port=args.port)
    await demo.run_demo()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())