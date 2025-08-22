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
            self._get_search_actions_tool(),
            self._get_search_enumerations_tool(),
            self._get_enumeration_fields_tool()
        ]
    
    def _get_search_entities_tool(self) -> Tool:
        """Get search entities tool definition."""
        return Tool(
            name="d365fo_search_entities",
            description="Search for D365 F&O data entities by name, pattern, or properties. D365 F&O entity names follow specific patterns - try multiple search strategies for best results. For customer groups, try patterns like 'Customer.*Group', 'Cust.*Group', '.*CustomerGroup.*', or search for 'Group' alone to find all group-related entities.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Regex pattern to search for in entity names. IMPORTANT: D365 F&O entity names have specific conventions. For customer groups, try: 'Customer.*Group', 'Cust.*Group', '.*CustomerGroup.*', 'Commission.*Group', or just 'Group' to find all group entities. For broader searches, use '.*Customer.*' or '.*' (with limit). Case-sensitive regex matching."
                    },
                    "entity_category": {
                        "type": "string",
                        "description": "Filter entities by their functional category (e.g., Master, Transaction).",
                        "enum": ["Master", "Document", "Transaction", "Reference", "Parameter"]
                    },
                    "data_service_enabled": {
                        "type": "boolean",
                        "description": "Filter entities that are enabled for OData API access (e.g., for querying)."
                    },
                    "data_management_enabled": {
                        "type": "boolean",
                        "description": "Filter entities that can be used with the Data Management Framework (DMF)."
                    },
                    "is_read_only": {
                        "type": "boolean",
                        "description": "Filter entities based on whether they are read-only or support write operations."
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 500,
                        "default": 100,
                        "description": "Maximum number of matching entities to return. Use smaller values (10-50) for initial exploration, larger values (100-500) for comprehensive searches."
                    }
                },
                "required": ["pattern"]
            }
        )
    
    def _get_entity_schema_tool(self) -> Tool:
        """Get entity schema tool definition."""
        return Tool(
            name="d365fo_get_entity_schema",
            description="Get the detailed schema for a specific D365 F&O data entity, including properties, keys, and available actions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "entityName": {
                        "type": "string",
                        "description": "The public name of the entity (e.g., 'CustomersV3')."
                    },
                    "include_properties": {
                        "type": "boolean",
                        "default": True,
                        "description": "Set to true to include detailed information about each property (field) in the entity."
                    },
                    "resolve_labels": {
                        "type": "boolean",
                        "default": True,
                        "description": "Set to true to resolve and include human-readable labels for the entity and its properties."
                    },
                    "language": {
                        "type": "string",
                        "default": "en-US",
                        "description": "The language to use for resolving labels (e.g., 'en-US', 'fr-FR')."
                    }
                },
                "required": ["entityName"]
            }
        )
    
    def _get_search_actions_tool(self) -> Tool:
        """Get search actions tool definition."""
        return Tool(
            name="d365fo_search_actions",
            description="Search for available OData actions in D365 F&O. Actions are operations that can be performed on entities or globally. Returns full action details including binding information for calling actions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Regex pattern to search for in action names. Use this for broad or partial name searches."
                    },
                    "entityName": {
                        "type": "string",
                        "description": "Optional. Filter actions that are bound to a specific data entity (e.g., 'CustomersV3')."
                    },
                    "bindingKind": {
                        "type": "string",
                        "description": "Optional. Filter by binding type: 'Unbound' (can call directly), 'BoundToEntitySet' (operates on entity collections), 'BoundToEntityInstance' (requires specific entity key).",
                        "enum": ["Unbound", "BoundToEntitySet", "BoundToEntityInstance"]
                    },
                    "isFunction": {
                        "type": "boolean",
                        "description": "Optional. Filter by type: 'true' for functions (read-only), 'false' for actions (may have side-effects). Note: This filter may not be fully supported yet."
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 500,
                        "default": 100,
                        "description": "Maximum number of matching actions to return."
                    }
                },
                "required": ["pattern"]
            }
        )
    
    def _get_search_enumerations_tool(self) -> Tool:
        """Get search enumerations tool definition."""
        return Tool(
            name="d365fo_search_enumerations",
            description="Search for enumerations (enums) in D365 F&O. Enums represent a list of named constants (e.g., NoYes, CustVendorBlocked).",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Regex pattern to search for in enumeration names (e.g., '.*Status.*')."
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 500,
                        "default": 100,
                        "description": "Maximum number of matching enumerations to return."
                    }
                },
                "required": ["pattern"]
            }
        )
    
    def _get_enumeration_fields_tool(self) -> Tool:
        """Get enumeration fields tool definition."""
        return Tool(
            name="d365fo_get_enumeration_fields",
            description="Get the detailed members (fields) and their values for a specific D365 F&O enumeration.",
            inputSchema={
                "type": "object",
                "properties": {
                    "enumeration_name": {
                        "type": "string",
                        "description": "The exact name of the enumeration (e.g., 'NoYes', 'CustVendorBlocked')."
                    },
                    "resolve_labels": {
                        "type": "boolean",
                        "default": True,
                        "description": "Set to true to resolve and include human-readable labels for the enumeration and its members."
                    },
                    "language": {
                        "type": "string",
                        "default": "en-US",
                        "description": "The language to use for resolving labels (e.g., 'en-US', 'fr-FR')."
                    }
                },
                "required": ["enumeration_name"]
            }
        )
    
    async def _try_fts_search(self, client, pattern: str) -> List[dict]:
        """Try FTS5 full-text search when regex search fails
        
        Args:
            client: FOClient instance with metadata cache
            pattern: Original search pattern
            
        Returns:
            List of entity dictionaries from FTS search
        """
        try:
            # Import here to avoid circular imports
            from ...metadata_cache import MetadataSearchEngine
            from ...models import SearchQuery
            
            # Create search engine if metadata cache is available
            if not client.metadata_cache:
                return []
                
            search_engine = MetadataSearchEngine(client.metadata_cache)
            
            # Extract search terms from regex pattern
            search_text = self._extract_search_terms(pattern)
            if not search_text:
                return []
            
            # Create search query for data entities
            query = SearchQuery(
                text=search_text,
                entity_types=["data_entity"],
                limit=5,  # Limit FTS suggestions
                use_fulltext=True
            )
            
            # Execute FTS search
            fts_results = await search_engine.search(query)
            
            # Convert search results to entity info
            fts_entities = []
            for result in fts_results.results:
                try:
                    # Get full entity info for each FTS result
                    entity_info = await client.get_data_entity_info(result.name)
                    if entity_info:
                        entity_dict = entity_info.to_dict()
                        # Add FTS metadata
                        entity_dict["fts_relevance"] = result.relevance
                        entity_dict["fts_snippet"] = result.snippet
                        fts_entities.append(entity_dict)
                except Exception:
                    # If entity info retrieval fails, skip this result
                    continue
            
            return fts_entities
            
        except Exception as e:
            logger.debug(f"FTS search failed: {e}")
            return []
    
    def _extract_search_terms(self, pattern: str) -> str:
        """Extract meaningful search terms from regex pattern
        
        Args:
            pattern: Regex pattern to extract terms from
            
        Returns:
            Space-separated search terms
        """
        import re
        
        # Remove regex operators and extract word-like terms
        # First, handle character classes like [Cc] -> C, [Gg] -> G
        cleaned = re.sub(r'\[([A-Za-z])\1\]', r'\1', pattern.replace('[Cc]', 'C').replace('[Gg]', 'G'))
        
        # Remove other regex characters
        cleaned = re.sub(r'[.*\\{}()|^$+?]', ' ', cleaned)
        
        # Extract words (sequences of letters, minimum 3 chars)
        words = re.findall(r'[A-Za-z]{3,}', cleaned)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_words = []
        for word in words:
            word_lower = word.lower()
            if word_lower not in seen and len(word) >= 3:
                seen.add(word_lower)
                unique_words.append(word)
        
        return ' '.join(unique_words[:3])  # Limit to first 3 unique terms
    
    async def execute_search_entities(self, arguments: dict) -> List[TextContent]:
        """Execute search entities tool.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            List of TextContent responses
        """
        try:
            profile = arguments.get("profile", "default")
            client = await self.client_manager.get_client(profile)
            
            start_time = time.time()
            
            # Use search_data_entities to support all the filtering options
            entities = await client.search_data_entities(
                pattern=arguments["pattern"],
                entity_category=arguments.get("entity_category"),
                data_service_enabled=arguments.get("data_service_enabled"),
                data_management_enabled=arguments.get("data_management_enabled"),  # Add this for completeness
                is_read_only=arguments.get("is_read_only")
            )
            
            # Convert DataEntityInfo objects to dictionaries for JSON serialization
            entity_dicts = []
            for entity in entities:
                entity_dict = entity.to_dict()
                entity_dicts.append(entity_dict)

            # Apply limit
            limit = arguments.get("limit")
            filtered_entities = entity_dicts
            if limit is not None:
                filtered_entities = entity_dicts[:limit]
            
            # If no results and pattern seems specific, try a broader search for suggestions
            broader_suggestions = []
            fts_suggestions = []
            if len(filtered_entities) == 0:
                try:
                    # Try FTS5 search if metadata cache is available
                    if client.metadata_cache:
                        fts_suggestions = await self._try_fts_search(client, arguments["pattern"])
                        
                except Exception:
                    pass  # Ignore errors in suggestion search
            
            search_time = time.time() - start_time
            
            # Add helpful guidance when no results found
            suggestions = []
            if len(filtered_entities) == 0:
                suggestions = [
                    "Try broader patterns like '.*Customer.*', '.*Group.*', or '.*' (with small limit)",
                    "Use category filters: entity_category='Master' for customer groups",
                    "Check data_service_enabled=True for API-accessible entities",
                    "Common D365 F&O patterns: 'Cust' for Customer, 'Vend' for Vendor, 'Ledger' for GL"
                ]
                
                # Add FTS-specific suggestions if FTS results were found
                if fts_suggestions:
                    suggestions.insert(0, f"Found {len(fts_suggestions)} entities using full-text search (see ftsMatches below)")
                elif client.metadata_cache:
                    suggestions.append("Full-text search attempted but found no matches - try simpler terms")
            
            
            response = {
                "entities": filtered_entities,
                "totalCount": len(entities),
                "returnedCount": len(filtered_entities),
                "searchTime": round(search_time, 3),
                "pattern": arguments["pattern"],
                "limit": limit,
                "filters": {
                    "entity_Category": arguments.get("entity_Category"),
                    "data_Service_Enabled": arguments.get("data_Service_Enabled"),
                    "data_Management_Enabled": arguments.get("data_Management_Enabled"),
                    "is_Read_Only": arguments.get("is_Read_Only")
                },
                "suggestions": suggestions if suggestions else None,
                "broaderMatches": broader_suggestions if broader_suggestions else None,
                "ftsMatches": fts_suggestions if fts_suggestions else None
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
            profile = arguments.get("profile", "default")
            client = await self.client_manager.get_client(profile)

            entity_name = arguments["entityName"]
            entity_info = await client.get_public_entity_info(entity_name)
            

            if not entity_info:
                raise ValueError(f"Entity not found: {entity_name}")
            
            logger.info(f"Retrieved entity info for {entity_info}")
            entity_info_dict = entity_info.to_dict()

            return [TextContent(
                type="text",
                text=json.dumps(entity_info_dict, indent=2)
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
            profile = arguments.get("profile", "default")
            client = await self.client_manager.get_client(profile)
            
            start_time = time.time()
            
            # Extract search parameters
            pattern = arguments["pattern"]
            entity_name = arguments.get("entityName")
            binding_kind = arguments.get("bindingKind")
            
            # Search actions with full details
            actions = await client.search_actions(
                pattern=pattern,
                entity_name=entity_name,
                binding_kind=binding_kind
            )
            
            # Apply limit
            limit = arguments.get("limit")
            filtered_actions = actions[:limit] if limit is not None else actions
            
            # Convert ActionInfo objects to dictionaries for JSON serialization
            detailed_actions = []
            for action in filtered_actions:
                action_dict = action.to_dict()
                
                # Add additional metadata for better usability
                action_dict.update({
                    "parameter_count": len(action.parameters),
                    "has_return_value": action.return_type is not None,
                    "return_type_name": action.return_type.type_name if action.return_type else None,
                    "is_bound": action.binding_kind != "Unbound",
                    "can_call_directly": action.binding_kind == "Unbound",
                    "requires_entity_key": action.binding_kind == "BoundToEntityInstance"
                })
                
                detailed_actions.append(action_dict)
            
            search_time = time.time() - start_time
            
            response = {
                "actions": detailed_actions,
                "total_count": len(actions),
                "returned_count": len(filtered_actions),
                "search_time": round(search_time, 3),
                "search_parameters": {
                    "pattern": pattern,
                    "entity_name": entity_name,
                    "binding_kind": binding_kind,
                    "limit": limit
                },
                "summary": {
                    "unbound_actions": len([a for a in filtered_actions if a.binding_kind == "Unbound"]),
                    "entity_set_bound": len([a for a in filtered_actions if a.binding_kind == "BoundToEntitySet"]),
                    "entity_instance_bound": len([a for a in filtered_actions if a.binding_kind == "BoundToEntityInstance"]),
                    "unique_entities": len(set(a.entity_name for a in filtered_actions if a.entity_name))
                }
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
    
    async def execute_search_enumerations(self, arguments: dict) -> List[TextContent]:
        """Execute search enumerations tool.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            List of TextContent responses
        """
        try:
            profile = arguments.get("profile", "default")
            client = await self.client_manager.get_client(profile)
            
            start_time = time.time()
            
            # Search for enumerations using the pattern
            enumerations = await client.search_public_enumerations(
                pattern=arguments["pattern"]
            )
            
            # Convert EnumerationInfo objects to dictionaries for JSON serialization
            enum_dicts = []
            for enum in enumerations:
                enum_dict = enum.to_dict()
                enum_dicts.append(enum_dict)
            
            # Apply limit
            limit = arguments.get("limit")

            filtered_enums = enum_dicts if limit is None else enum_dicts[:limit]
            search_time = time.time() - start_time
            
            response = {
                "enumerations": filtered_enums,
                "totalCount": len(enumerations),
                "searchTime": round(search_time, 3),
                "pattern": arguments["pattern"],
                "limit": limit
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(response, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Search enumerations failed: {e}")
            error_response = {
                "error": str(e),
                "tool": "d365fo_search_enumerations",
                "arguments": arguments
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_response, indent=2)
            )]
    
    async def execute_get_enumeration_fields(self, arguments: dict) -> List[TextContent]:
        """Execute get enumeration fields tool.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            List of TextContent responses
        """
        try:
            profile = arguments.get("profile", "default")
            client = await self.client_manager.get_client(profile)
            
            enumeration_name = arguments["enumeration_name"]
            resolve_labels = arguments.get("resolve_labels", True)
            language = arguments.get("language", "en-US")
            
            # Get detailed enumeration information
            enum_info = await client.get_public_enumeration_info(
                enumeration_name=enumeration_name,
                resolve_labels=resolve_labels,
                language=language
            )
            
            if not enum_info:
                raise ValueError(f"Enumeration not found: {enumeration_name}")
            
            # Convert to dictionary for JSON serialization
            enum_dict = enum_info.to_dict()
            
            # Add additional metadata
            response = {
                "enumeration": enum_dict,
                "memberCount": len(enum_info.members),
                "hasLabels": bool(enum_info.label_text),
                "language": language if resolve_labels else None
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(response, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Get enumeration fields failed: {e}")
            error_response = {
                "error": str(e),
                "tool": "d365fo_get_enumeration_fields",
                "arguments": arguments
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_response, indent=2)
            )]