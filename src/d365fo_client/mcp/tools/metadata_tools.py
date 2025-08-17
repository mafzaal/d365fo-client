"""Metadata tools for MCP server."""

import json
import logging
import time
from typing import List
from mcp import Tool
from mcp.types import TextContent

from ..client_manager import D365FOClientManager


logger = logging.getLogger(__name__)


class MetadataTools:
    """Metadata management tools for the MCP server."""
    
    def __init__(self, client_manager: D365FOClientManager):
        """Initialize metadata tools.
        
        Args:
            client_manager: D365FO client manager instance
        """
        self.client_manager = client_manager
    
    def get_tools(self) -> List[Tool]:
        """Get list of metadata tools.
        
        Returns:
            List of Tool definitions
        """
        return [
            self._get_search_entities_tool(),
            self._get_entity_schema_tool(),
            self._get_search_actions_tool()
        ]
    
    def _get_search_entities_tool(self) -> Tool:
        """Get search entities tool definition."""
        return Tool(
            name="d365fo_search_entities",
            description="Search for entities by name or pattern",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Search pattern for entity names"
                    },
                    "entityCategory": {
                        "type": "string",
                        "description": "Filter by entity category",
                        "enum": ["Master", "Document", "Transaction", "Reference", "Parameter"]
                    },
                    "dataServiceEnabled": {
                        "type": "boolean",
                        "description": "Filter by data service enabled"
                    },
                    "isReadOnly": {
                        "type": "boolean",
                        "description": "Filter by read-only status"
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 500,
                        "default": 100,
                        "description": "Maximum number of results"
                    }
                },
                "required": ["pattern"]
            }
        )
    
    def _get_entity_schema_tool(self) -> Tool:
        """Get entity schema tool definition."""
        return Tool(
            name="d365fo_get_entity_schema",
            description="Get detailed schema information for a specific entity",
            inputSchema={
                "type": "object",
                "properties": {
                    "entityName": {
                        "type": "string",
                        "description": "Name of the entity"
                    },
                    "includeProperties": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include property details"
                    },
                    "resolveLabels": {
                        "type": "boolean",
                        "default": True,
                        "description": "Resolve label texts"
                    },
                    "language": {
                        "type": "string",
                        "default": "en-US",
                        "description": "Language for label resolution"
                    }
                },
                "required": ["entityName"]
            }
        )
    
    def _get_search_actions_tool(self) -> Tool:
        """Get search actions tool definition."""
        return Tool(
            name="d365fo_search_actions",
            description="Search for available OData actions",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Search pattern for action names"
                    },
                    "entityName": {
                        "type": "string",
                        "description": "Filter by entity name"
                    },
                    "isFunction": {
                        "type": "boolean",
                        "description": "Filter by function vs action"
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 500,
                        "default": 100,
                        "description": "Maximum number of results"
                    }
                },
                "required": ["pattern"]
            }
        )
    
    async def execute_search_entities(self, arguments: dict) -> List[TextContent]:
        """Execute search entities tool.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            List of TextContent responses
        """
        try:
            client = await self.client_manager.get_client()
            
            start_time = time.time()
            entities = client.search_entities(arguments["pattern"])
            
            # Apply filters if provided
            limit = arguments.get("limit", 100)
            filtered_entities = entities[:limit]
            
            # Get detailed info for entities
            detailed_entities = []
            for entity_name in filtered_entities:
                entity_info = client.get_entity_info(entity_name)
                if entity_info:
                    detailed_entities.append({
                        "name": entity_info.name,
                        "entitySetName": entity_info.entity_set_name,
                        "keys": entity_info.keys,
                        "propertyCount": len(entity_info.properties),
                        "isReadOnly": entity_info.is_read_only,
                        "labelText": entity_info.label_text,
                        "entityCategory": getattr(entity_info, 'entity_category', 'Unknown')
                    })
            
            search_time = time.time() - start_time
            
            response = {
                "entities": detailed_entities,
                "totalCount": len(entities),
                "searchTime": round(search_time, 3),
                "pattern": arguments["pattern"],
                "limit": limit
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(response, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Search entities failed: {e}")
            error_response = {
                "error": str(e),
                "tool": "d365fo_search_entities",
                "arguments": arguments
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_response, indent=2)
            )]
    
    async def execute_get_entity_schema(self, arguments: dict) -> List[TextContent]:
        """Execute get entity schema tool.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            List of TextContent responses
        """
        try:
            client = await self.client_manager.get_client()
            
            entity_name = arguments["entityName"]
            entity_info = client.get_entity_info(entity_name)
            
            if not entity_info:
                raise ValueError(f"Entity not found: {entity_name}")
            
            # Build detailed schema response
            response = {
                "entity": {
                    "name": entity_info.name,
                    "entitySetName": entity_info.entity_set_name,
                    "labelText": entity_info.label_text,
                    "isReadOnly": entity_info.is_read_only,
                    "entityCategory": getattr(entity_info, 'entity_category', 'Unknown')
                },
                "properties": [
                    {
                        "name": prop.name,
                        "type": prop.type,
                        "isKey": prop.name in entity_info.keys,
                        "maxLength": getattr(prop, 'max_length', None),
                        "labelText": getattr(prop, 'label_text', None) if arguments.get("resolveLabels", True) else None
                    } for prop in entity_info.properties
                ] if arguments.get("includeProperties", True) else [],
                "keys": entity_info.keys,
                "propertyCount": len(entity_info.properties)
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(response, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Get entity schema failed: {e}")
            error_response = {
                "error": str(e),
                "tool": "d365fo_get_entity_schema",
                "arguments": arguments
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_response, indent=2)
            )]
    
    async def execute_search_actions(self, arguments: dict) -> List[TextContent]:
        """Execute search actions tool.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            List of TextContent responses
        """
        try:
            client = await self.client_manager.get_client()
            
            start_time = time.time()
            actions = client.search_actions(arguments["pattern"])
            
            # Apply limit
            limit = arguments.get("limit", 100)
            filtered_actions = actions[:limit]
            
            # Get detailed info for actions
            detailed_actions = []
            for action_name in filtered_actions:
                action_info = client.get_action_info(action_name)
                if action_info:
                    detailed_actions.append({
                        "name": action_info.name,
                        "isFunction": getattr(action_info, 'is_function', False),
                        "isBound": getattr(action_info, 'is_bound', False),
                        "parameterCount": len(getattr(action_info, 'parameters', [])),
                        "returnType": getattr(action_info, 'return_type', 'void')
                    })
            
            search_time = time.time() - start_time
            
            response = {
                "actions": detailed_actions,
                "totalCount": len(actions),
                "searchTime": round(search_time, 3),
                "pattern": arguments["pattern"],
                "limit": limit
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(response, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Search actions failed: {e}")
            error_response = {
                "error": str(e),
                "tool": "d365fo_search_actions", 
                "arguments": arguments
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_response, indent=2)
            )]