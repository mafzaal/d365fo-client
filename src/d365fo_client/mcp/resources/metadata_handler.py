"""Metadata resource handler for MCP server."""

import json
import logging
from datetime import datetime
from typing import List
from mcp.types import Resource

from ..client_manager import D365FOClientManager


logger = logging.getLogger(__name__)


class MetadataResourceHandler:
    """Handles metadata resources for the MCP server."""
    
    def __init__(self, client_manager: D365FOClientManager):
        """Initialize the metadata resource handler.
        
        Args:
            client_manager: D365FO client manager instance
        """
        self.client_manager = client_manager
    
    async def list_resources(self) -> List[Resource]:
        """List available metadata resources.
        
        Returns:
            List of metadata resources
        """
        resources = [
            Resource(
                uri="d365fo://metadata/entities",
                name="Data Entities Metadata",
                description="All data entities metadata and schemas",
                mimeType="application/json"
            ),
            Resource(
                uri="d365fo://metadata/actions",
                name="OData Actions",
                description="Available OData actions and functions",
                mimeType="application/json"
            ),
            Resource(
                uri="d365fo://metadata/enumerations",
                name="System Enumerations",
                description="System enumerations and their values",
                mimeType="application/json"
            ),
            Resource(
                uri="d365fo://metadata/labels",
                name="System Labels",
                description="System labels and translations",
                mimeType="application/json"
            )
        ]
        
        logger.info(f"Listed {len(resources)} metadata resources")
        return resources
    
    async def read_resource(self, uri: str) -> str:
        """Read specific metadata resource.
        
        Args:
            uri: Resource URI
            
        Returns:
            JSON string with metadata resource content
        """
        try:
            if uri == "d365fo://metadata/entities":
                return await self._get_entities_metadata()
            elif uri == "d365fo://metadata/actions":
                return await self._get_actions_metadata()
            elif uri == "d365fo://metadata/enumerations":
                return await self._get_enumerations_metadata()
            elif uri == "d365fo://metadata/labels":
                return await self._get_labels_metadata()
            else:
                raise ValueError(f"Unknown metadata resource URI: {uri}")
        except Exception as e:
            logger.error(f"Failed to read metadata resource {uri}: {e}")
            error_content = {
                "error": str(e),
                "uri": uri,
                "timestamp": datetime.utcnow().isoformat()
            }
            return json.dumps(error_content, indent=2)
    
    async def _get_entities_metadata(self) -> str:
        """Get entities metadata resource."""
        try:
            client = await self.client_manager.get_client()
            
            # Get all entities
            entities = client.search_entities("")
            
            # Get detailed info for first 50 entities (performance limit)
            detailed_entities = []
            for entity_name in entities[:50]:
                entity_info = client.get_entity_info(entity_name)
                if entity_info:
                    detailed_entities.append({
                        "name": entity_info.name,
                        "entitySetName": entity_info.entity_set_name,
                        "keys": entity_info.keys,
                        "propertyCount": len(entity_info.properties),
                        "isReadOnly": entity_info.is_read_only,
                        "labelText": entity_info.label_text
                    })
            
            metadata_content = {
                "type": "entities",
                "count": len(entities),
                "detailedItems": detailed_entities,
                "totalEntities": len(entities),
                "lastUpdated": datetime.utcnow().isoformat(),
                "statistics": {
                    "readOnlyCount": sum(1 for e in detailed_entities if e["isReadOnly"]),
                    "writableCount": sum(1 for e in detailed_entities if not e["isReadOnly"])
                }
            }
            
            return json.dumps(metadata_content, indent=2)
        except Exception as e:
            logger.error(f"Failed to get entities metadata: {e}")
            raise
    
    async def _get_actions_metadata(self) -> str:
        """Get actions metadata resource."""
        try:
            client = await self.client_manager.get_client()
            
            # Get all actions
            actions = client.search_actions("")
            
            # Get detailed info for first 50 actions (performance limit)
            detailed_actions = []
            for action_name in actions[:50]:
                action_info = client.get_action_info(action_name)
                if action_info:
                    detailed_actions.append({
                        "name": action_info.name,
                        "isFunction": getattr(action_info, 'is_function', False),
                        "isBound": getattr(action_info, 'is_bound', False),
                        "parameterCount": len(getattr(action_info, 'parameters', [])),
                        "returnType": getattr(action_info, 'return_type', 'void')
                    })
            
            metadata_content = {
                "type": "actions",
                "count": len(actions),
                "detailedItems": detailed_actions,
                "totalActions": len(actions),
                "lastUpdated": datetime.utcnow().isoformat(),
                "statistics": {
                    "functionsCount": sum(1 for a in detailed_actions if a["isFunction"]),
                    "actionsCount": sum(1 for a in detailed_actions if not a["isFunction"]),
                    "boundCount": sum(1 for a in detailed_actions if a["isBound"])
                }
            }
            
            return json.dumps(metadata_content, indent=2)
        except Exception as e:
            logger.error(f"Failed to get actions metadata: {e}")
            raise
    
    async def _get_enumerations_metadata(self) -> str:
        """Get enumerations metadata resource."""
        try:
            client = await self.client_manager.get_client()
            
            # Try to get public enumerations
            try:
                enumerations = await client.get_public_enumerations()
                detailed_enums = []
                
                for enum_info in enumerations[:50]:  # Limit for performance
                    detailed_enums.append({
                        "name": enum_info.name,
                        "valueCount": len(enum_info.members) if hasattr(enum_info, 'members') else 0,
                        "description": getattr(enum_info, 'description', '')
                    })
            except Exception:
                # Fallback if public enumerations not available
                detailed_enums = []
            
            metadata_content = {
                "type": "enumerations", 
                "count": len(detailed_enums),
                "detailedItems": detailed_enums,
                "totalEnumerations": len(detailed_enums),
                "lastUpdated": datetime.utcnow().isoformat()
            }
            
            return json.dumps(metadata_content, indent=2)
        except Exception as e:
            logger.error(f"Failed to get enumerations metadata: {e}")
            raise
    
    async def _get_labels_metadata(self) -> str:
        """Get labels metadata resource."""
        try:
            # For now, return basic label information
            # In a full implementation, we'd query the label cache
            metadata_content = {
                "type": "labels",
                "count": 0,  # TODO: Get actual label count
                "detailedItems": [],
                "totalLabels": 0,
                "lastUpdated": datetime.utcnow().isoformat(),
                "supportedLanguages": ["en-US", "en-GB", "de-DE", "fr-FR", "es-ES"],
                "note": "Label metadata requires metadata sync to be populated"
            }
            
            return json.dumps(metadata_content, indent=2)
        except Exception as e:
            logger.error(f"Failed to get labels metadata: {e}")
            raise