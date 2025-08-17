"""CRUD operation tools for MCP server."""

import json
import logging
import time
from typing import List, Dict, Any, Union
from mcp import Tool
from mcp.types import TextContent

from ..client_manager import D365FOClientManager
from ...models import QueryOptions


logger = logging.getLogger(__name__)


class CrudTools:
    """CRUD operation tools for the MCP server."""
    
    def __init__(self, client_manager: D365FOClientManager):
        """Initialize CRUD tools.
        
        Args:
            client_manager: D365FO client manager instance
        """
        self.client_manager = client_manager
    
    def get_tools(self) -> List[Tool]:
        """Get list of CRUD tools.
        
        Returns:
            List of Tool definitions
        """
        return [
            self._get_query_entities_tool(),
            self._get_entity_record_tool(),
            self._get_create_record_tool(),
            self._get_update_record_tool(),
            self._get_delete_record_tool()
        ]
    
    def _get_query_entities_tool(self) -> Tool:
        """Get query entities tool definition."""
        return Tool(
            name="d365fo_query_entities",
            description="Query D365FO entities with advanced OData parameters",
            inputSchema={
                "type": "object",
                "properties": {
                    "entityName": {
                        "type": "string",
                        "description": "Name of the entity to query"
                    },
                    "select": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Fields to select"
                    },
                    "filter": {
                        "type": "string",
                        "description": "OData filter expression"
                    },
                    "expand": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Related entities to expand"
                    },
                    "orderBy": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Order by fields"
                    },
                    "top": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 1000,
                        "description": "Number of records to return"
                    },
                    "skip": {
                        "type": "integer",
                        "minimum": 0,
                        "description": "Number of records to skip"
                    },
                    "count": {
                        "type": "boolean",
                        "description": "Include total count in response"
                    }
                },
                "required": ["entityName"]
            }
        )
    
    def _get_entity_record_tool(self) -> Tool:
        """Get entity record tool definition."""
        return Tool(
            name="d365fo_get_entity_record",
            description="Get a specific entity record by key",
            inputSchema={
                "type": "object",
                "properties": {
                    "entityName": {
                        "type": "string",
                        "description": "Name of the entity"
                    },
                    "key": {
                        "oneOf": [
                            {"type": "string"},
                            {"type": "object"}
                        ],
                        "description": "Record key (string or object)"
                    },
                    "select": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Fields to select"
                    },
                    "expand": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Related entities to expand"
                    }
                },
                "required": ["entityName", "key"]
            }
        )
    
    def _get_create_record_tool(self) -> Tool:
        """Get create record tool definition."""
        return Tool(
            name="d365fo_create_entity_record",
            description="Create a new entity record",
            inputSchema={
                "type": "object",
                "properties": {
                    "entityName": {
                        "type": "string",
                        "description": "Name of the entity"
                    },
                    "data": {
                        "type": "object",
                        "description": "Record data to create"
                    },
                    "returnRecord": {
                        "type": "boolean",
                        "description": "Return the created record",
                        "default": False
                    }
                },
                "required": ["entityName", "data"]
            }
        )
    
    def _get_update_record_tool(self) -> Tool:
        """Get update record tool definition."""
        return Tool(
            name="d365fo_update_entity_record",
            description="Update an existing entity record",
            inputSchema={
                "type": "object",
                "properties": {
                    "entityName": {
                        "type": "string",
                        "description": "Name of the entity"
                    },
                    "key": {
                        "oneOf": [
                            {"type": "string"},
                            {"type": "object"}
                        ],
                        "description": "Record key (string or object)"
                    },
                    "data": {
                        "type": "object",
                        "description": "Record data to update"
                    },
                    "returnRecord": {
                        "type": "boolean",
                        "description": "Return the updated record",
                        "default": False
                    },
                    "ifMatch": {
                        "type": "string",
                        "description": "ETag for optimistic concurrency"
                    }
                },
                "required": ["entityName", "key", "data"]
            }
        )
    
    def _get_delete_record_tool(self) -> Tool:
        """Get delete record tool definition."""
        return Tool(
            name="d365fo_delete_entity_record",
            description="Delete an entity record",
            inputSchema={
                "type": "object",
                "properties": {
                    "entityName": {
                        "type": "string",
                        "description": "Name of the entity"
                    },
                    "key": {
                        "oneOf": [
                            {"type": "string"},
                            {"type": "object"}
                        ],
                        "description": "Record key (string or object)"
                    },
                    "ifMatch": {
                        "type": "string",
                        "description": "ETag for optimistic concurrency"
                    }
                },
                "required": ["entityName", "key"]
            }
        )
    
    async def execute_query_entities(self, arguments: dict) -> List[TextContent]:
        """Execute query entities tool.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            List of TextContent responses
        """
        try:
            client = await self.client_manager.get_client()
            
            # Build query options
            options = QueryOptions(
                select=arguments.get("select"),
                filter=arguments.get("filter"),
                expand=arguments.get("expand"),
                order_by=arguments.get("orderBy"),
                top=arguments.get("top", 100),
                skip=arguments.get("skip"),
                count=arguments.get("count", False)
            )
            
            # Execute query
            start_time = time.time()
            result = await client.get_entities(
                arguments["entityName"], 
                options=options
            )
            query_time = time.time() - start_time
            
            # Format response
            response = {
                "data": result.get("value", []),
                "count": result.get("@odata.count"),
                "nextLink": result.get("@odata.nextLink"),
                "queryTime": round(query_time, 3),
                "totalRecords": len(result.get("value", []))
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(response, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Query entities failed: {e}")
            error_response = {
                "error": str(e),
                "tool": "d365fo_query_entities",
                "arguments": arguments
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_response, indent=2)
            )]
    
    async def execute_get_entity_record(self, arguments: dict) -> List[TextContent]:
        """Execute get entity record tool.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            List of TextContent responses
        """
        try:
            client = await self.client_manager.get_client()
            
            start_time = time.time()
            record = await client.get_entity_by_key(
                arguments["entityName"],
                arguments["key"],
                select=arguments.get("select"),
                expand=arguments.get("expand")
            )
            retrieval_time = time.time() - start_time
            
            response = {
                "record": record,
                "found": record is not None,
                "retrievalTime": round(retrieval_time, 3)
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(response, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Get entity record failed: {e}")
            error_response = {
                "error": str(e),
                "tool": "d365fo_get_entity_record",
                "arguments": arguments
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_response, indent=2)
            )]
    
    async def execute_create_entity_record(self, arguments: dict) -> List[TextContent]:
        """Execute create entity record tool.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            List of TextContent responses
        """
        try:
            client = await self.client_manager.get_client()
            
            result = await client.create_entity(
                arguments["entityName"],
                arguments["data"]
            )
            
            response = {
                "success": True,
                "recordId": result.get("id") if result else None,
                "createdRecord": result if arguments.get("returnRecord", False) else None,
                "validationErrors": None
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(response, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Create entity record failed: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "tool": "d365fo_create_entity_record",
                "arguments": arguments
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_response, indent=2)
            )]
    
    async def execute_update_entity_record(self, arguments: dict) -> List[TextContent]:
        """Execute update entity record tool.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            List of TextContent responses
        """
        try:
            client = await self.client_manager.get_client()
            
            result = await client.update_entity(
                arguments["entityName"],
                arguments["key"],
                arguments["data"]
            )
            
            response = {
                "success": True,
                "updatedRecord": result if arguments.get("returnRecord", False) else None,
                "validationErrors": None,
                "conflictDetected": False
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(response, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Update entity record failed: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "tool": "d365fo_update_entity_record",
                "arguments": arguments
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_response, indent=2)
            )]
    
    async def execute_delete_entity_record(self, arguments: dict) -> List[TextContent]:
        """Execute delete entity record tool.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            List of TextContent responses
        """
        try:
            client = await self.client_manager.get_client()
            
            await client.delete_entity(
                arguments["entityName"],
                arguments["key"]
            )
            
            response = {
                "success": True,
                "conflictDetected": False,
                "error": None
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(response, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Delete entity record failed: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "tool": "d365fo_delete_entity_record",
                "arguments": arguments
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_response, indent=2)
            )]