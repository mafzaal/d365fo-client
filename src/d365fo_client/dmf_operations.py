"""Data Management Framework (DMF) operations for D365 F&O client."""

import json
import logging
from typing import Any, Dict, List, Optional

from .exceptions import DMFError
from .models import (
    DMFExecutionStatus,
    DMFExecutionSummary,
    DMFExportOptions,
    DMFImportOptions,
)
from .session import SessionManager

logger = logging.getLogger(__name__)


class DmfOperations:
    """Handles Data Management Framework (DMF) operations for D365 F&O.

    All DMF actions are bound to the DataManagementDefinitionGroups entity set.
    This class provides a high-level interface for data import/export operations,
    package management, and execution monitoring.
    """

    ENTITY_SET_NAME = "DataManagementDefinitionGroups"
    ACTION_PREFIX = "Microsoft.Dynamics.DataEntities"

    def __init__(self, session_manager: SessionManager, base_url: str):
        """Initialize DMF operations.

        Args:
            session_manager: HTTP session manager
            base_url: Base F&O URL
        """
        self.session_manager = session_manager
        self.base_url = base_url.rstrip("/")
        self.logger = logging.getLogger(__name__)

    def _build_action_url(self, action_name: str) -> str:
        """Build URL for DMF action (all are BoundToEntitySet).

        Args:
            action_name: Action name without prefix

        Returns:
            Complete action URL
        """
        return f"{self.base_url}/data/{self.ENTITY_SET_NAME}/{self.ACTION_PREFIX}.{action_name}"

    async def _call_action(
        self, action_name: str, parameters: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Call a DMF action method.

        Args:
            action_name: Action name (without prefix)
            parameters: Action parameters

        Returns:
            Action result

        Raises:
            DMFError: If action execution fails
        """
        session = await self.session_manager.get_session()
        url = self._build_action_url(action_name)
        body = parameters or {}

        self.logger.debug(f"Calling DMF action: {action_name} with params: {body}")

        try:
            async with session.post(url, json=body) as response:
                if response.status in [200, 201]:
                    content_type = response.headers.get("content-type", "")
                    if "application/json" in content_type:
                        result = await response.json()
                        self.logger.debug(f"Action {action_name} succeeded")
                        return result
                    else:
                        result = await response.text()
                        self.logger.debug(f"Action {action_name} succeeded (text)")
                        return result
                elif response.status == 204:
                    self.logger.debug(f"Action {action_name} succeeded (no content)")
                    return {"success": True}
                else:
                    error_text = await response.text()
                    self.logger.error(
                        f"DMF action {action_name} failed: {response.status} - {error_text}"
                    )
                    raise DMFError(
                        f"DMF action {action_name} failed: {response.status} - {error_text}"
                    )
        except DMFError:
            raise
        except Exception as e:
            self.logger.error(f"DMF action {action_name} error: {e}")
            raise DMFError(f"DMF action {action_name} error: {str(e)}") from e

    # ========================================================================
    # EXPORT OPERATIONS
    # ========================================================================

    async def export_to_package(
        self,
        definition_group_id: str,
        package_name: str,
        execution_id: str = "",
        re_execute: bool = False,
        legal_entity_id: str = "",
    ) -> str:
        """Export data to package (synchronous).

        Args:
            definition_group_id: Definition group identifier
            package_name: Name for the package
            execution_id: Existing execution ID (for re-execution)
            re_execute: Whether to re-execute existing export
            legal_entity_id: Legal entity (company) to export from

        Returns:
            Execution ID for tracking
        """
        params = {
            "definitionGroupId": definition_group_id,
            "packageName": package_name,
            "executionId": execution_id,
            "reExecute": re_execute,
            "legalEntityId": legal_entity_id,
        }
        return await self._call_action("ExportToPackage", params)

    async def export_to_package_async(
        self,
        definition_group_id: str,
        package_name: str,
        execution_id: str = "",
        re_execute: bool = False,
        legal_entity_id: str = "",
        entity_list: str = "",
    ) -> str:
        """Export data to package (asynchronous).

        Args:
            definition_group_id: Definition group identifier
            package_name: Name for the package
            execution_id: Existing execution ID (for re-execution)
            re_execute: Whether to re-execute existing export
            legal_entity_id: Legal entity (company) to export from
            entity_list: Comma-separated list of entities to export

        Returns:
            Execution ID for tracking
        """
        params = {
            "definitionGroupId": definition_group_id,
            "packageName": package_name,
            "executionId": execution_id,
            "reExecute": re_execute,
            "legalEntityId": legal_entity_id,
            "entityList": entity_list,
        }
        return await self._call_action("ExportToPackageAsync", params)

    async def export_to_package_preview(
        self,
        definition_group_id: str,
        package_name: str,
        execution_id: str = "",
        re_execute: bool = False,
        legal_entity_id: str = "",
        export_preview_count: int = 100,
    ) -> str:
        """Export data to package with preview/sampling.

        Args:
            definition_group_id: Definition group identifier
            package_name: Name for the package
            execution_id: Existing execution ID (for re-execution)
            re_execute: Whether to re-execute existing export
            legal_entity_id: Legal entity (company) to export from
            export_preview_count: Number of records to preview

        Returns:
            Execution ID for tracking
        """
        params = {
            "definitionGroupId": definition_group_id,
            "packageName": package_name,
            "executionId": execution_id,
            "reExecute": re_execute,
            "legalEntityId": legal_entity_id,
            "exportPreviewCount": export_preview_count,
        }
        return await self._call_action("ExportToPackagePreview", params)

    async def export_to_package_preview_async(
        self,
        definition_group_id: str,
        package_name: str,
        execution_id: str = "",
        re_execute: bool = False,
        legal_entity_id: str = "",
        export_preview_count: int = 100,
    ) -> str:
        """Export data to package with preview (asynchronous).

        Args:
            definition_group_id: Definition group identifier
            package_name: Name for the package
            execution_id: Existing execution ID (for re-execution)
            re_execute: Whether to re-execute existing export
            legal_entity_id: Legal entity (company) to export from
            export_preview_count: Number of records to preview

        Returns:
            Execution ID for tracking
        """
        params = {
            "definitionGroupId": definition_group_id,
            "packageName": package_name,
            "executionId": execution_id,
            "reExecute": re_execute,
            "legalEntityId": legal_entity_id,
            "exportPreviewCount": export_preview_count,
        }
        return await self._call_action("ExportToPackagePreviewAsync", params)

    async def export_to_package_delta(
        self,
        definition_group_id: str,
        package_name: str,
        execution_id: str = "",
        re_execute: bool = False,
        legal_entity_id: str = "",
        entity_list: str = "",
    ) -> str:
        """Export only changed data (delta export).

        Args:
            definition_group_id: Definition group identifier
            package_name: Name for the package
            execution_id: Existing execution ID (for re-execution)
            re_execute: Whether to re-execute existing export
            legal_entity_id: Legal entity (company) to export from
            entity_list: Comma-separated list of entities to export

        Returns:
            Execution ID for tracking
        """
        params = {
            "definitionGroupId": definition_group_id,
            "packageName": package_name,
            "executionId": execution_id,
            "reExecute": re_execute,
            "legalEntityId": legal_entity_id,
            "entityList": entity_list,
        }
        return await self._call_action("ExportToPackageDelta", params)

    async def export_from_package(
        self,
        package_url: str,
        definition_group_id: str,
        execution_id: str = "",
        execute: bool = True,
        overwrite: bool = False,
        legal_entity_id: str = "",
    ) -> str:
        """Export using package template.

        Args:
            package_url: URL to package template
            definition_group_id: Definition group identifier
            execution_id: Existing execution ID
            execute: Whether to execute immediately
            overwrite: Whether to overwrite existing data
            legal_entity_id: Legal entity (company) to export from

        Returns:
            Execution ID for tracking
        """
        params = {
            "packageUrl": package_url,
            "definitionGroupId": definition_group_id,
            "executionId": execution_id,
            "execute": execute,
            "overwrite": overwrite,
            "legalEntityId": legal_entity_id,
        }
        return await self._call_action("ExportFromPackage", params)

    async def get_exported_package_url(self, execution_id: str) -> str:
        """Get download URL for exported package.

        Args:
            execution_id: Execution ID from export operation

        Returns:
            Download URL for the package
        """
        params = {"executionId": execution_id}
        return await self._call_action("GetExportedPackageUrl", params)

    # ========================================================================
    # IMPORT OPERATIONS
    # ========================================================================

    async def import_from_package(
        self,
        package_url: str,
        definition_group_id: str,
        execution_id: str = "",
        execute: bool = True,
        overwrite: bool = False,
        legal_entity_id: str = "",
    ) -> str:
        """Import data from package.

        Args:
            package_url: URL to package file
            definition_group_id: Definition group identifier
            execution_id: Existing execution ID
            execute: Whether to execute immediately
            overwrite: Whether to overwrite existing data
            legal_entity_id: Legal entity (company) to import to

        Returns:
            Execution ID for tracking
        """
        params = {
            "packageUrl": package_url,
            "definitionGroupId": definition_group_id,
            "executionId": execution_id,
            "execute": execute,
            "overwrite": overwrite,
            "legalEntityId": legal_entity_id,
        }
        return await self._call_action("ImportFromPackage", params)

    async def import_from_dmt_package(
        self,
        package_url: str,
        definition_group_id: str,
        execution_id: str = "",
        execute: bool = True,
        overwrite: bool = False,
        legal_entity_id: str = "",
        import_batch_group_id: str = "",
        fail_on_error: bool = False,
    ) -> str:
        """Import from Data Migration Toolkit (DMT) package.

        Args:
            package_url: URL to DMT package file
            definition_group_id: Definition group identifier
            execution_id: Existing execution ID
            execute: Whether to execute immediately
            overwrite: Whether to overwrite existing data
            legal_entity_id: Legal entity (company) to import to
            import_batch_group_id: Batch group for import processing
            fail_on_error: Whether to fail entire import on any error

        Returns:
            Execution ID for tracking
        """
        params = {
            "packageUrl": package_url,
            "definitionGroupId": definition_group_id,
            "executionId": execution_id,
            "execute": execute,
            "overwrite": overwrite,
            "legalEntityId": legal_entity_id,
            "importBatchGroupId": import_batch_group_id,
            "failOnError": fail_on_error,
        }
        return await self._call_action("ImportFromDMTPackage", params)

    # ========================================================================
    # INITIALIZATION OPERATIONS
    # ========================================================================

    async def initialize_data_management(self) -> None:
        """Initialize Data Management Framework (synchronous)."""
        await self._call_action("InitializeDataManagement", {})

    async def initialize_data_management_async(self) -> None:
        """Initialize Data Management Framework (asynchronous)."""
        await self._call_action("InitializeDataManagementAsync", {})

    # ========================================================================
    # STATUS & MONITORING OPERATIONS
    # ========================================================================

    async def get_execution_summary_status(self, execution_id: str) -> Dict[str, Any]:
        """Get overall execution status.

        Args:
            execution_id: Execution ID to check

        Returns:
            Execution summary status object
        """
        params = {"executionId": execution_id}
        return await self._call_action("GetExecutionSummaryStatus", params)

    async def get_entity_execution_summary_status_list(
        self, execution_id: str
    ) -> List[str]:
        """Get per-entity status list.

        Args:
            execution_id: Execution ID to check

        Returns:
            List of entity execution statuses
        """
        params = {"executionId": execution_id}
        return await self._call_action("GetEntityExecutionSummaryStatusList", params)

    async def get_message_status(self, message_id: str) -> Dict[str, Any]:
        """Get message queue status.

        Args:
            message_id: Message ID to check

        Returns:
            Message status object
        """
        params = {"messageId": message_id}
        return await self._call_action("GetMessageStatus", params)

    # ========================================================================
    # ERROR MANAGEMENT OPERATIONS
    # ========================================================================

    async def get_execution_errors(self, execution_id: str) -> str:
        """Get execution error details.

        Args:
            execution_id: Execution ID to check

        Returns:
            Error details as JSON string
        """
        params = {"executionId": execution_id}
        result = await self._call_action("GetExecutionErrors", params)
        if isinstance(result, dict) and "value" in result:
            return result["value"]
        return result

    async def get_import_target_error_keys_file_url(
        self, execution_id: str, entity_name: str
    ) -> str:
        """Get target error keys file URL.

        Args:
            execution_id: Execution ID
            entity_name: Entity name

        Returns:
            URL to error keys file
        """
        params = {"executionId": execution_id, "entityName": entity_name}
        return await self._call_action("GetImportTargetErrorKeysFileUrl", params)

    async def get_import_staging_error_file_url(
        self, execution_id: str, entity_name: str
    ) -> str:
        """Get staging error file URL.

        Args:
            execution_id: Execution ID
            entity_name: Entity name

        Returns:
            URL to staging error file
        """
        params = {"executionId": execution_id, "entityName": entity_name}
        return await self._call_action("GetImportStagingErrorFileUrl", params)

    async def generate_import_target_error_keys_file(
        self, execution_id: str, entity_name: str
    ) -> bool:
        """Generate error keys file for failed records.

        Args:
            execution_id: Execution ID
            entity_name: Entity name

        Returns:
            True if file generation succeeded
        """
        params = {"executionId": execution_id, "entityName": entity_name}
        return await self._call_action("GenerateImportTargetErrorKeysFile", params)

    # ========================================================================
    # UTILITY OPERATIONS
    # ========================================================================

    async def get_azure_write_url(self, unique_file_name: str) -> str:
        """Get Azure Blob Storage write URL.

        Args:
            unique_file_name: Unique file name for the blob

        Returns:
            Azure Blob Storage write URL with SAS token
        """
        params = {"uniqueFileName": unique_file_name}
        result = await self._call_action("GetAzureWriteUrl", params)
        
        # Parse nested JSON response if needed
        if isinstance(result, dict) and "value" in result:
            try:
                import json
                inner_json = json.loads(result["value"])
                return inner_json.get("BlobUrl", "")
            except (json.JSONDecodeError, TypeError):
                self.logger.warning("Failed to parse inner JSON from GetAzureWriteUrl")
                return result.get("value", "")
        
        return result

    async def get_entity_sequence(self, list_of_data_entities: str) -> str:
        """Get recommended entity execution sequence.

        Args:
            list_of_data_entities: Comma-separated list of entity names

        Returns:
            Recommended execution sequence (JSON)
        """
        params = {"listOfDataEntities": list_of_data_entities}
        result = await self._call_action("GetEntitySequence", params)
        if isinstance(result, dict) and "value" in result:
            return result["value"]
        return result

    async def reset_version_token(
        self, definition_group_id: str, entity_name: str, source_name: str
    ) -> bool:
        """Reset change tracking version token.

        Args:
            definition_group_id: Definition group identifier
            entity_name: Entity name
            source_name: Data source name

        Returns:
            True if reset succeeded
        """
        params = {
            "definitionGroupId": definition_group_id,
            "entityName": entity_name,
            "sourceName": source_name,
        }
        return await self._call_action("ResetVersionToken", params)

    async def get_execution_id_by_message_id(self, message_id: str) -> str:
        """Map message ID to execution ID.

        Args:
            message_id: Message ID (GUID)

        Returns:
            Execution ID
        """
        params = {"_messageId": message_id}
        return await self._call_action("GetExecutionIdByMessageId", params)
