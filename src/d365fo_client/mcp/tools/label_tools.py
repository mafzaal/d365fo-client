"""Label tools for MCP server."""

import json
import logging
import time
from typing import List

from mcp import Tool
from mcp.types import TextContent

from ..client_manager import D365FOClientManager

logger = logging.getLogger(__name__)


class LabelTools:
    """Label and localization tools for the MCP server."""

    def __init__(self, client_manager: D365FOClientManager):
        """Initialize label tools.

        Args:
            client_manager: D365FO client manager instance
        """
        self.client_manager = client_manager

    def get_tools(self) -> List[Tool]:
        """Get list of label tools.

        Returns:
            List of Tool definitions
        """
        return [self._get_label_tool(), self._get_labels_batch_tool()]

    def _get_label_tool(self) -> Tool:
        """Get label tool definition."""
        return Tool(
            name="d365fo_get_label",
            description="Get label text by label ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "labelId": {
                        "type": "string",
                        "description": "Label ID (e.g., @SYS1234)",
                    },
                    "language": {
                        "type": "string",
                        "default": "en-US",
                        "description": "Language code for label text",
                    },
                    "fallbackToEnglish": {
                        "type": "boolean",
                        "default": True,
                        "description": "Fallback to English if translation not found",
                    },
                    "profile": {
                        "type": "string",
                        "description": "Configuration profile to use (optional - uses default profile if not specified)",
                    },
                },
                "required": ["labelId"],
            },
        )

    def _get_labels_batch_tool(self) -> Tool:
        """Get labels batch tool definition."""
        return Tool(
            name="d365fo_get_labels_batch",
            description="Get multiple labels in a single request",
            inputSchema={
                "type": "object",
                "properties": {
                    "labelIds": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of label IDs to retrieve",
                    },
                    "language": {
                        "type": "string",
                        "default": "en-US",
                        "description": "Language code for label texts",
                    },
                    "fallbackToEnglish": {
                        "type": "boolean",
                        "default": True,
                        "description": "Fallback to English if translation not found",
                    },
                    "profile": {
                        "type": "string",
                        "description": "Configuration profile to use (optional - uses default profile if not specified)",
                    },
                },
                "required": ["labelIds"],
            },
        )

    async def execute_get_label(self, arguments: dict) -> List[TextContent]:
        """Execute get label tool.

        Args:
            arguments: Tool arguments

        Returns:
            List of TextContent responses
        """
        try:
            profile = arguments.get("profile", "default")
            client = await self.client_manager.get_client(profile)

            label_id = arguments["labelId"]
            language = arguments.get("language", "en-US")

            # Get label text
            label_text = await client.get_label_text(label_id, language=language)

            response = {
                "labelId": label_id,
                "text": label_text or f"[{label_id}]",
                "language": language,
                "found": label_text is not None,
            }

            return [TextContent(type="text", text=json.dumps(response, indent=2))]

        except Exception as e:
            logger.error(f"Get label failed: {e}")
            error_response = {
                "error": str(e),
                "tool": "d365fo_get_label",
                "arguments": arguments,
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]

    async def execute_get_labels_batch(self, arguments: dict) -> List[TextContent]:
        """Execute get labels batch tool.

        Args:
            arguments: Tool arguments

        Returns:
            List of TextContent responses
        """
        try:
            profile = arguments.get("profile", "default")
            client = await self.client_manager.get_client(profile)

            label_ids = arguments["labelIds"]
            language = arguments.get("language", "en-US")

            start_time = time.time()

            # Get labels in batch
            labels = {}
            missing_labels = []

            for label_id in label_ids:
                try:
                    label_text = await client.get_label_text(
                        label_id, language=language
                    )
                    if label_text:
                        labels[label_id] = label_text
                    else:
                        missing_labels.append(label_id)
                except Exception:
                    missing_labels.append(label_id)

            retrieval_time = time.time() - start_time

            response = {
                "labels": labels,
                "missingLabels": missing_labels,
                "retrievalTime": round(retrieval_time, 3),
                "language": language,
                "totalRequested": len(label_ids),
                "foundCount": len(labels),
            }

            return [TextContent(type="text", text=json.dumps(response, indent=2))]

        except Exception as e:
            logger.error(f"Get labels batch failed: {e}")
            error_response = {
                "error": str(e),
                "tool": "d365fo_get_labels_batch",
                "arguments": arguments,
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
