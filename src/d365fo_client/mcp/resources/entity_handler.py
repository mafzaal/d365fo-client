"""Entity resource handler for MCP server."""

import json
import logging
from datetime import datetime
from typing import List
from mcp.types import Resource

from ..client_manager import D365FOClientManager


logger = logging.getLogger(__name__)


class EntityResourceHandler:
    """Handles entity resources for the MCP server."""
    
    def __init__(self, client_manager: D365FOClientManager):
        """Initialize the entity resource handler.
        
        Args:
            client_manager: D365FO client manager instance
        """
        self.client_manager = client_manager
    
    async def list_resources(self) -> List[Resource]:
        """List available entity resources.
        
        Returns:
            List of entity resources
        """
        try:
            client = await self.client_manager.get_client()
            entities = client.search_entities("")
            
            resources = []
            for entity_name in entities[:100]:  # Limit to first 100 for performance
                resources.append(Resource(
                    uri=f"d365fo://entities/{entity_name}",
                    name=f"Entity: {entity_name}",
                    description=f"D365FO entity {entity_name} with metadata and sample data",
                    mimeType="application/json"
                ))
            
            logger.info(f"Listed {len(resources)} entity resources")
            return resources
        except Exception as e:
            logger.error(f"Failed to list entity resources: {e}")
            raise
    
    async def read_resource(self, uri: str) -> str:
        """Read specific entity resource.
        
        Args:
            uri: Resource URI (e.g., "d365fo://entities/Customers")
            
        Returns:
            JSON string with entity resource content
        """
        entity_name = self._extract_entity_name(uri)
        client = await self.client_manager.get_client()
        
        try:
            # Get entity metadata
            entity_info = client.get_entity_info(entity_name)
            
            # Get sample data (limited to 5 records)
            from ...models import QueryOptions
            sample_data = await client.get_entities(
                entity_name, 
                options=QueryOptions(top=5)
            )
            
            # Build resource content
            resource_content = {
                "metadata": {
                    "name": entity_info.name if entity_info else entity_name,
                    "entitySetName": entity_info.entity_set_name if entity_info else entity_name,
                    "keys": entity_info.keys if entity_info else [],
                    "properties": [
                        {
                            "name": prop.name,
                            "type": prop.type,
                            "isKey": prop.name in (entity_info.keys if entity_info else []),
                            "maxLength": getattr(prop, 'max_length', None),
                            "label": getattr(prop, 'label_text', None)
                        } for prop in (entity_info.properties if entity_info else [])
                    ],
                    "isReadOnly": entity_info.is_read_only if entity_info else False,
                    "labelText": entity_info.label_text if entity_info else None
                } if entity_info else None,
                "sampleData": sample_data.get("value", []) if sample_data else [],
                "recordCount": sample_data.get("@odata.count") if sample_data else None,
                "lastUpdated": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Retrieved entity resource: {entity_name}")
            return json.dumps(resource_content, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to read entity resource {entity_name}: {e}")
            # Return error in resource format
            error_content = {
                "error": str(e),
                "entityName": entity_name,
                "timestamp": datetime.utcnow().isoformat()
            }
            return json.dumps(error_content, indent=2)
    
    def _extract_entity_name(self, uri: str) -> str:
        """Extract entity name from resource URI.
        
        Args:
            uri: Resource URI
            
        Returns:
            Entity name
        """
        if uri.startswith("d365fo://entities/"):
            return uri[len("d365fo://entities/"):]
        raise ValueError(f"Invalid entity resource URI: {uri}")