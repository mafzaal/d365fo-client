"""Query resource handler for MCP server."""

import json
import logging
from datetime import datetime
from typing import List

from mcp.types import Resource

from ..client_manager import D365FOClientManager

logger = logging.getLogger(__name__)


class QueryResourceHandler:
    """Handles query resources for the MCP server."""

    def __init__(self, client_manager: D365FOClientManager):
        """Initialize the query resource handler.

        Args:
            client_manager: D365FO client manager instance
        """
        self.client_manager = client_manager
        # Predefined query templates
        self.query_templates = {
            "customers_recent": {
                "entity_name": "Customers",
                "description": "Recent customer records",
                "select": ["CustomerAccount", "Name", "CreatedDateTime"],
                "order_by": ["CreatedDateTime desc"],
                "top": 50,
            },
            "sales_orders_today": {
                "entity_name": "SalesOrders",
                "description": "Sales orders created today",
                "filter": "CreatedDateTime ge {today}",
                "select": ["SalesOrderNumber", "CustomerAccount", "TotalAmount"],
                "template": True,
                "parameters": [
                    {
                        "name": "today",
                        "type": "datetime",
                        "required": True,
                        "description": "Today's date in ISO format",
                    }
                ],
            },
            "vendors_active": {
                "entity_name": "Vendors",
                "description": "Active vendor records",
                "filter": "Status eq 'Active'",
                "select": ["VendorAccount", "Name", "PaymentTerms"],
                "top": 100,
            },
        }

    async def list_resources(self) -> List[Resource]:
        """List available query resources.

        Returns:
            List of query resources
        """
        resources = []

        for query_name, query_config in self.query_templates.items():
            resources.append(
                Resource(
                    uri=f"d365fo://queries/{query_name}",
                    name=f"Query: {query_name}",
                    description=query_config["description"],
                    mimeType="application/json",
                )
            )

        logger.info(f"Listed {len(resources)} query resources")
        return resources

    async def read_resource(self, uri: str) -> str:
        """Read specific query resource.

        Args:
            uri: Resource URI (e.g., "d365fo://queries/customers_recent")

        Returns:
            JSON string with query resource content
        """
        query_name = self._extract_query_name(uri)

        try:
            if query_name not in self.query_templates:
                raise ValueError(f"Unknown query template: {query_name}")

            query_config = self.query_templates[query_name]

            # Build query resource content
            resource_content = {
                "queryName": query_name,
                "entityName": query_config["entity_name"],
                "description": query_config["description"],
                "select": query_config.get("select"),
                "filter": query_config.get("filter"),
                "expand": query_config.get("expand"),
                "orderBy": query_config.get("order_by"),
                "top": query_config.get("top"),
                "skip": query_config.get("skip"),
                "template": query_config.get("template", False),
                "parameters": query_config.get("parameters", []),
                "lastUpdated": datetime.utcnow().isoformat(),
            }

            logger.info(f"Retrieved query resource: {query_name}")
            return json.dumps(resource_content, indent=2)

        except Exception as e:
            logger.error(f"Failed to read query resource {query_name}: {e}")
            error_content = {
                "error": str(e),
                "queryName": query_name,
                "timestamp": datetime.utcnow().isoformat(),
            }
            return json.dumps(error_content, indent=2)

    def _extract_query_name(self, uri: str) -> str:
        """Extract query name from resource URI.

        Args:
            uri: Resource URI

        Returns:
            Query name
        """
        if uri.startswith("d365fo://queries/"):
            return uri[len("d365fo://queries/") :]
        raise ValueError(f"Invalid query resource URI: {uri}")
