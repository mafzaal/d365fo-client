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
            self._get_delete_record_tool(),
            self._get_call_action_tool()
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
                    "profile": {
                        "type": "string",
                        "description": "Configuration profile to use",
                        "default": "default"
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
    
    def _get_call_action_tool(self) -> Tool:
        """Get call action tool definition."""
        return Tool(
            name="d365fo_call_action",
            description="Call/invoke a D365FO OData action with optional parameters and entity binding",
            inputSchema={
                "type": "object",
                "properties": {
                    "actionName": {
                        "type": "string",
                        "description": "Name of the action to call (e.g., 'Microsoft.Dynamics.DataEntities.GetKeys')"
                    },
                    "profile": {
                        "type": "string",
                        "description": "Configuration profile to use",
                        "default": "default"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Action parameters as key-value pairs"
                    },
                    "entityName": {
                        "type": "string",
                        "description": "Entity name for bound actions (optional)"
                    },
                    "entityKey": {
                        "oneOf": [
                            {"type": "string"},
                            {"type": "object"}
                        ],
                        "description": "Entity key for bound actions (optional, string or composite key object)"
                    },
                    "bindingKind": {
                        "type": "string",
                        "description": "Specify binding kind if known: 'Unbound', 'BoundToEntitySet', 'BoundToEntity'",
                        "enum": ["Unbound", "BoundToEntitySet", "BoundToEntity"]
                    },
                    "timeout": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 300,
                        "default": 30,
                        "description": "Request timeout in seconds"
                    }
                },
                "required": ["actionName"]
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
            profile = arguments.get("profile", "default")
            client = await self.client_manager.get_client(profile)
            
            # Build query options
            options = QueryOptions(
                select=arguments.get("select"),
                filter=arguments.get("filter"),
                expand=arguments.get("expand"),
                orderby=arguments.get("orderBy"),
                top=arguments.get("top", None),
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
    
    async def execute_call_action(self, arguments: dict) -> List[TextContent]:
        """Execute call action tool.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            List of TextContent responses
        """
        try:
            profile = arguments.get("profile", "default")
            client = await self.client_manager.get_client(profile)
            
            action_name = arguments["actionName"]
            parameters = arguments.get("parameters", {})
            entity_name = arguments.get("entityName")
            entity_key = arguments.get("entityKey")
            binding_kind = arguments.get("bindingKind")
            
            # Log the action call attempt
            logger.info(f"Calling action: {action_name}")
            if entity_name:
                logger.info(f"  Entity: {entity_name}")
            if entity_key:
                logger.info(f"  Key: {entity_key}")
            if binding_kind:
                logger.info(f"  Binding: {binding_kind}")
            
            start_time = time.time()
            
            # Call the action using the client's call_action method
            result = await client.call_action(
                action_name=action_name,
                parameters=parameters,
                entity_name=entity_name,
                entity_key=entity_key
            )
            
            execution_time = time.time() - start_time
            
            # Format response
            response = {
                "success": True,
                "actionName": action_name,
                "result": result,
                "executionTime": round(execution_time, 3),
                "parameters": parameters,
                "binding": {
                    "entityName": entity_name,
                    "entityKey": entity_key,
                    "bindingKind": binding_kind
                } if entity_name or entity_key else None
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(response, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Call action failed: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "tool": "d365fo_call_action",
                "actionName": arguments.get("actionName"),
                "arguments": arguments
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_response, indent=2)
            )]