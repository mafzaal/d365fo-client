import asyncio
import logging
import os

from mcp.server.fastmcp import FastMCP

from d365fo_client.mcp.fastmcp_server import FastD365FOMCPServer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    # Initialize Server
    mcp = FastMCP("D365FO Demo")
    server = FastD365FOMCPServer(mcp)

    # List tools
    tools = server.mcp._tool_manager.list_tools()
    logger.info(f"Registered {len(tools)} tools")

    dmf_tools = [t for t in tools if "dmf" in t.name]
    logger.info("DMF Tools:")
    for t in dmf_tools:
        logger.info(f" - {t.name}: {t.description[:50]}...")

    # Note: To run actual tools, we would need a client connection
    # This demo just verifies registration


if __name__ == "__main__":
    asyncio.run(main())
