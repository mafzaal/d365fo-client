#!/usr/bin/env python3
"""
Web Integration Example - HTTP Transport

This example demonstrates how to integrate the FastMCP D365FO server
with web applications using HTTP transport.

Prerequisites:
1. Start the FastMCP server with HTTP transport:
   d365fo-fastmcp-server --transport http --port 8000

2. Install required dependencies:
   pip install aiohttp

Usage:
   python examples/web_integration_http.py
"""

import asyncio
import json
from typing import Any, Dict, Optional

import aiohttp


class D365FOWebClient:
    """Web client for D365FO FastMCP server via HTTP transport."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the web client.

        Args:
            base_url: Base URL of the FastMCP HTTP server
        """
        self.base_url = base_url
        self.mcp_endpoint = f"{base_url}/mcp"
        self._session: Optional[aiohttp.ClientSession] = None
        self._request_id = 1

    async def __aenter__(self):
        """Async context manager entry."""
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()

    def _get_request_id(self) -> int:
        """Get next request ID."""
        request_id = self._request_id
        self._request_id += 1
        return request_id

    async def call_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call a D365FO MCP tool via HTTP.

        Args:
            tool_name: Name of the MCP tool to call
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        if not self._session:
            raise RuntimeError(
                "Client not initialized. Use 'async with' context manager."
            )

        mcp_request = {
            "jsonrpc": "2.0",
            "id": self._get_request_id(),
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }

        async with self._session.post(
            self.mcp_endpoint,
            json=mcp_request,
            headers={"Content-Type": "application/json"},
        ) as response:
            if response.status != 200:
                raise Exception(f"HTTP {response.status}: {await response.text()}")

            result = await response.json()

            if "error" in result:
                raise Exception(f"MCP Error: {result['error']}")

            return result.get("result", {})

    async def list_tools(self) -> Dict[str, Any]:
        """List available MCP tools."""
        if not self._session:
            raise RuntimeError(
                "Client not initialized. Use 'async with' context manager."
            )

        mcp_request = {
            "jsonrpc": "2.0",
            "id": self._get_request_id(),
            "method": "tools/list",
        }

        async with self._session.post(
            self.mcp_endpoint,
            json=mcp_request,
            headers={"Content-Type": "application/json"},
        ) as response:
            result = await response.json()
            return result.get("result", {})

    async def get_resource(self, uri: str) -> Dict[str, Any]:
        """Get an MCP resource."""
        if not self._session:
            raise RuntimeError(
                "Client not initialized. Use 'async with' context manager."
            )

        mcp_request = {
            "jsonrpc": "2.0",
            "id": self._get_request_id(),
            "method": "resources/read",
            "params": {"uri": uri},
        }

        async with self._session.post(
            self.mcp_endpoint,
            json=mcp_request,
            headers={"Content-Type": "application/json"},
        ) as response:
            result = await response.json()
            return result.get("result", {})


async def demo_basic_operations():
    """Demonstrate basic D365FO operations via HTTP."""
    print("🌐 D365FO FastMCP HTTP Integration Demo")
    print("=" * 50)

    async with D365FOWebClient() as client:
        try:
            # 1. List available tools
            print("\n1. 📋 Listing available tools...")
            tools_result = await client.list_tools()
            tools = tools_result.get("tools", [])
            print(f"   Found {len(tools)} tools")

            # Show first few tools
            for tool in tools[:5]:
                print(f"   - {tool['name']}: {tool['description'][:60]}...")

            # 2. Test connection
            print("\n2. 🔌 Testing D365FO connection...")
            connection_result = await client.call_tool("d365fo_test_connection", {})

            if connection_result.get("success"):
                print("   ✅ Connection successful!")
                print(
                    f"   Response time: {connection_result.get('response_time_ms', 'N/A')}ms"
                )
            else:
                print("   ❌ Connection failed")
                print(
                    f"   Error: {connection_result.get('error_message', 'Unknown error')}"
                )

            # 3. Get environment info
            print("\n3. 🏢 Getting environment information...")
            env_result = await client.call_tool("d365fo_get_environment_info", {})

            if env_result.get("success"):
                env_info = env_result.get("environment_info", {})
                print(f"   Environment: {env_info.get('base_url', 'N/A')}")
                print(
                    f"   Application Version: {env_info.get('application_version', 'N/A')}"
                )
                print(f"   Platform Version: {env_info.get('platform_version', 'N/A')}")
            else:
                print("   ❌ Failed to get environment info")
                print(f"   Error: {env_result.get('error_message', 'Unknown error')}")

            # 4. Search for customer entities
            print("\n4. 🔍 Searching for customer entities...")
            search_result = await client.call_tool(
                "d365fo_search_entities",
                {"pattern": "customer", "limit": 5, "data_service_enabled": True},
            )

            if search_result.get("success"):
                entities = search_result.get("entities", [])
                print(f"   Found {len(entities)} customer-related entities:")
                for entity in entities:
                    print(
                        f"   - {entity.get('name', 'N/A')}: {entity.get('label_text', 'N/A')}"
                    )
            else:
                print("   ❌ Entity search failed")
                print(
                    f"   Error: {search_result.get('error_message', 'Unknown error')}"
                )

            # 5. Get entity schema (if entities found)
            if search_result.get("success") and search_result.get("entities"):
                entity_name = search_result["entities"][0].get("public_entity_name")
                if entity_name:
                    print(f"\n5. 📊 Getting schema for entity: {entity_name}")
                    schema_result = await client.call_tool(
                        "d365fo_get_entity_schema",
                        {"entityName": entity_name, "include_properties": True},
                    )

                    if schema_result.get("success"):
                        schema = schema_result.get("schema", {})
                        properties = schema.get("properties", [])
                        print(f"   Entity: {schema.get('name', 'N/A')}")
                        print(f"   Properties: {len(properties)}")
                        print(f"   Read-only: {schema.get('is_read_only', 'N/A')}")

                        # Show key properties
                        key_props = [p for p in properties if p.get("is_key", False)]
                        if key_props:
                            print(
                                f"   Key fields: {', '.join(p['name'] for p in key_props)}"
                            )
                    else:
                        print("   ❌ Schema retrieval failed")
                        print(
                            f"   Error: {schema_result.get('error_message', 'Unknown error')}"
                        )

            # 6. Access environment status resource
            print("\n6. 📈 Accessing environment status resource...")
            try:
                resource_result = await client.get_resource(
                    "d365fo://environment/status"
                )
                if resource_result.get("contents"):
                    content = resource_result["contents"][0]
                    print(f"   Resource type: {content.get('mimeType', 'N/A')}")
                    print(
                        f"   Content length: {len(content.get('text', ''))} characters"
                    )
                else:
                    print("   ❌ No resource content found")
            except Exception as e:
                print(f"   ⚠️  Resource access error: {e}")

        except Exception as e:
            print(f"❌ Demo failed: {e}")
            import traceback

            traceback.print_exc()


async def demo_customer_query():
    """Demonstrate customer data querying via HTTP."""
    print("\n" + "=" * 50)
    print("🔍 Customer Data Query Demo")
    print("=" * 50)

    async with D365FOWebClient() as client:
        try:
            # Query customer entities with OData options
            print("\n1. 👥 Querying customer data...")
            query_result = await client.call_tool(
                "d365fo_query_entities",
                {
                    "entityName": "CustomersV3",
                    "select": ["CustomerAccount", "Name", "SalesCurrencyCode"],
                    "top": 5,
                    "orderby": ["Name"],
                },
            )

            if query_result.get("success"):
                records = query_result.get("records", [])
                print(f"   Retrieved {len(records)} customer records:")

                for i, record in enumerate(records, 1):
                    print(
                        f"   {i}. {record.get('CustomerAccount', 'N/A')} - {record.get('Name', 'N/A')} ({record.get('SalesCurrencyCode', 'N/A')})"
                    )
            else:
                print("   ❌ Customer query failed")
                print(f"   Error: {query_result.get('error_message', 'Unknown error')}")

                # This is expected if no D365FO environment is configured
                if (
                    "authentication"
                    in str(query_result.get("error_message", "")).lower()
                ):
                    print(
                        "   ℹ️  This is expected without proper D365FO environment configuration"
                    )

        except Exception as e:
            print(f"   ⚠️  Query error: {e}")


async def demo_profile_management():
    """Demonstrate profile management via HTTP."""
    print("\n" + "=" * 50)
    print("⚙️  Profile Management Demo")
    print("=" * 50)

    async with D365FOWebClient() as client:
        try:
            # List existing profiles
            print("\n1. 📋 Listing existing profiles...")
            profiles_result = await client.call_tool("d365fo_list_profiles", {})

            if profiles_result.get("success"):
                profiles = profiles_result.get("profiles", [])
                print(f"   Found {len(profiles)} profiles:")
                for profile in profiles:
                    is_default = " (default)" if profile.get("is_default") else ""
                    print(f"   - {profile.get('name', 'N/A')}{is_default}")
            else:
                print("   ❌ Profile listing failed")
                print(
                    f"   Error: {profiles_result.get('error_message', 'Unknown error')}"
                )

            # Get default profile info
            print("\n2. 🎯 Getting default profile...")
            default_result = await client.call_tool("d365fo_get_default_profile", {})

            if default_result.get("success"):
                profile = default_result.get("profile", {})
                print(f"   Default profile: {profile.get('name', 'N/A')}")
                print(f"   Base URL: {profile.get('base_url', 'N/A')}")
                print(f"   Auth mode: {profile.get('auth_mode', 'N/A')}")
            else:
                print("   ❌ Default profile retrieval failed")
                print(
                    f"   Error: {default_result.get('error_message', 'Unknown error')}"
                )

        except Exception as e:
            print(f"   ⚠️  Profile management error: {e}")


async def main():
    """Main demo function."""
    print("🚀 FastMCP D365FO HTTP Integration Examples")
    print("=" * 60)
    print("This demo shows how to integrate D365FO with web applications")
    print("using the FastMCP server's HTTP transport.")
    print("\nPrerequisites:")
    print("1. Start FastMCP server: d365fo-fastmcp-server --transport http --port 8000")
    print("2. Ensure aiohttp is installed: pip install aiohttp")
    print()

    try:
        # Run all demos
        await demo_basic_operations()
        await demo_customer_query()
        await demo_profile_management()

        print("\n" + "=" * 60)
        print("✅ All HTTP integration demos completed!")
        print("\n💡 Integration Tips:")
        print("   - Use HTTP transport for RESTful web service integration")
        print("   - Implement proper error handling for production systems")
        print("   - Consider authentication and authorization for web deployments")
        print("   - Use connection pooling for high-throughput applications")
        print("   - Monitor response times and implement timeouts")

    except aiohttp.ClientError as e:
        print(f"\n❌ Connection Error: {e}")
        print("\n🔧 Troubleshooting:")
        print(
            "   1. Ensure FastMCP server is running: d365fo-fastmcp-server --transport http --port 8000"
        )
        print("   2. Check if port 8000 is available and not blocked by firewall")
        print("   3. Verify the server started without errors")

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())
