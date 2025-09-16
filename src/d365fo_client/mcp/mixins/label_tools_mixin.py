"""Label tools mixin for FastMCP server."""

import json
import logging
from typing import List

from .base_tools_mixin import BaseToolsMixin

logger = logging.getLogger(__name__)


class LabelToolsMixin(BaseToolsMixin):
    """Label retrieval tools for FastMCP server."""
    
    def register_label_tools(self):
        """Register all label tools with FastMCP."""
        
        @self.mcp.tool()
        async def d365fo_get_label(
            labelId: str,
            language: str = "en-US",
            profile: str = "default",
        ) -> str:
            """Get label text by label ID.

            Args:
                labelId: Label ID (e.g., @SYS1234)
                language: Language code for label text
                fallbackToEnglish: Fallback to English if translation not found
                profile: Optional profile name

            Returns:
                JSON string with label text
            """
            try:
                client = await self._get_client(profile)

                # Get label
                label_text = await client.get_label_text(
                    label_id=labelId,
                    language=language,
                )

                return json.dumps(
                    {"labelId": labelId, "language": language, "labelText": label_text},
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Get label failed: {e}")
                return json.dumps({"error": str(e), "labelId": labelId}, indent=2)

        @self.mcp.tool()
        async def d365fo_get_labels_batch(
            labelIds: List[str],
            language: str = "en-US",
            profile: str = "default",
        ) -> str:
            """Get multiple labels in a single request.

            Args:
                labelIds: List of label IDs to retrieve
                language: Language code for label texts
                fallbackToEnglish: Fallback to English if translation not found
                profile: Optional profile name

            Returns:
                JSON string with label texts
            """
            try:
                client = await self._get_client(profile)

                # Get labels batch
                labels = await client.get_labels_batch(
                    label_ids=labelIds,
                    language=language,
                )

                return json.dumps(
                    {
                        "language": language,
                        "totalRequested": len(labelIds),
                        "labels": labels,
                    },
                    indent=2,
                )

            except Exception as e:
                logger.error(f"Get labels batch failed: {e}")
                return json.dumps({"error": str(e), "labelIds": labelIds}, indent=2)