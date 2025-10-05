# Data Management Framework (DMF) Operations Implementation Specification

## Document Information
- **Version**: 1.0
- **Date**: October 5, 2025
- **Status**: Specification
- **Entity**: DataManagementDefinitionGroup
- **Total Actions**: 25 actions

## Executive Summary

This specification defines the implementation of Data Management Framework (DMF) operations for the d365fo-client package. The DMF provides comprehensive data import/export, package management, and execution tracking capabilities for Dynamics 365 Finance & Operations.

All 25 actions are **BoundToEntitySet**, meaning they operate on the `DataManagementDefinitionGroups` collection. This implementation will expose these operations through the `FOClient` class and create a dedicated `DmfToolsMixin` for FastMCP server integration.

## Table of Contents
1. [Action Categories](#action-categories)
2. [Architecture Overview](#architecture-overview)
3. [FOClient Implementation](#foclient-implementation)
4. [MCP Tools Mixin Implementation](#mcp-tools-mixin-implementation)
5. [Data Models](#data-models)
6. [Error Handling](#error-handling)
7. [Testing Strategy](#testing-strategy)
8. [Documentation Requirements](#documentation-requirements)

## Action Categories

The 25 actions are organized into 7 functional categories:

### 1. Export Operations (7 actions)
- `ExportToPackage` - Export data to package (synchronous)
- `ExportToPackageAsync` - Export data to package (asynchronous)
- `ExportToPackagePreview` - Export with preview/sampling
- `ExportToPackagePreviewAsync` - Export preview (asynchronous)
- `ExportToPackageDelta` - Export only changed data (delta)
- `ExportFromPackage` - Export using package template
- `GetExportedPackageUrl` - Get download URL for exported package

### 2. Import Operations (2 actions)
- `ImportFromPackage` - Import data from package
- `ImportFromDMTPackage` - Import from Data Migration Toolkit package

### 3. Initialization Operations (2 actions)
- `InitializeDataManagement` - Initialize DMF (synchronous)
- `InitializeDataManagementAsync` - Initialize DMF (asynchronous)

### 4. Status & Monitoring (3 actions)
- `GetExecutionSummaryStatus` - Get overall execution status
- `GetEntityExecutionSummaryStatusList` - Get per-entity status list
- `GetMessageStatus` - Get message queue status

### 5. Error Management (4 actions)
- `GetExecutionErrors` - Get execution error details
- `GetImportTargetErrorKeysFileUrl` - Get target error keys file URL
- `GetImportStagingErrorFileUrl` - Get staging error file URL
- `GenerateImportTargetErrorKeysFile` - Generate error keys file

### 6. Utility Operations (6 actions)
- `GetAzureWriteUrl` - Get Azure Blob Storage write URL
- `GetEntitySequence` - Get recommended entity execution sequence
- `ResetVersionToken` - Reset change tracking version token
- `GetExecutionIdByMessageId` - Map message ID to execution ID

### 7. Reserved for Future Use (1 action)
- (Future expansion category)

## Architecture Overview

### Component Structure
```
d365fo-client/
├── src/d365fo_client/
│   ├── client.py                          # Add DMF operations
│   ├── dmf_operations.py                  # NEW: DMF operations class
│   ├── models.py                          # Add DMF data models
│   └── mcp/
│       └── mixins/
│           ├── __init__.py                # Export DmfToolsMixin
│           └── dmf_tools_mixin.py        # NEW: DMF tools for FastMCP
├── docs/
│   └── DMF_OPERATIONS_IMPLEMENTATION_SPEC.md  # This document
├── examples/
│   ├── dmf_operations_example.py         # NEW: Usage examples
│   └── dmf_mcp_demo.py                   # NEW: MCP demo
└── tests/
    ├── unit/
    │   └── test_dmf_operations.py        # NEW: Unit tests
    └── integration/
        └── test_dmf_integration.py       # NEW: Integration tests
```

### Design Principles
1. **Separation of Concerns**: DMF operations in dedicated class
2. **Consistent API**: Follow existing FOClient patterns
3. **Type Safety**: Full type hints and validation
4. **Error Handling**: Comprehensive error handling with context
5. **Async/Await**: Full async support throughout
6. **Logging**: Detailed logging for debugging and monitoring
7. **Documentation**: Comprehensive docstrings and examples

## FOClient Implementation

### 1. DmfOperations Class

Create new file: `src/d365fo_client/dmf_operations.py`

```python
"""Data Management Framework (DMF) operations for D365 F&O client."""

import logging
from typing import Any, Dict, List, Optional

from .exceptions import DMFError, FOClientError
from .models import (
    DMFExecutionStatus,
    DMFExportOptions,
    DMFImportOptions,
    DMFExecutionSummary,
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
        self, 
        action_name: str, 
        parameters: Optional[Dict[str, Any]] = None
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

    async def get_execution_summary_status(
        self, execution_id: str
    ) -> Dict[str, Any]:
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
        return await self._call_action("GetExecutionErrors", params)

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
        return await self._call_action("GetAzureWriteUrl", params)

    async def get_entity_sequence(self, list_of_data_entities: str) -> str:
        """Get recommended entity execution sequence.
        
        Args:
            list_of_data_entities: Comma-separated list of entity names
            
        Returns:
            Recommended execution sequence (JSON)
        """
        params = {"listOfDataEntities": list_of_data_entities}
        return await self._call_action("GetEntitySequence", params)

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
```

### 2. FOClient Integration

Update `src/d365fo_client/client.py` to include DMF operations:

```python
# Add to imports
from .dmf_operations import DmfOperations

# Add to __init__ method
class FOClient:
    def __init__(self, config: Union[FOClientConfig, str, Dict[str, Any]]):
        # ... existing code ...
        
        # Initialize DMF operations
        self.dmf_ops = DmfOperations(self.session_manager, config.base_url)
    
    # Add DMF operation methods (delegate to dmf_ops)
    
    # Export operations
    async def export_to_package(
        self,
        definition_group_id: str,
        package_name: str,
        execution_id: str = "",
        re_execute: bool = False,
        legal_entity_id: str = "",
    ) -> str:
        """Export data to package (synchronous).
        
        See DmfOperations.export_to_package for full documentation.
        """
        await self._ensure_metadata_initialized()
        return await self.dmf_ops.export_to_package(
            definition_group_id, package_name, execution_id, re_execute, legal_entity_id
        )
    
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
        
        See DmfOperations.export_to_package_async for full documentation.
        """
        await self._ensure_metadata_initialized()
        return await self.dmf_ops.export_to_package_async(
            definition_group_id, package_name, execution_id, 
            re_execute, legal_entity_id, entity_list
        )
    
    # ... Add similar delegate methods for all 25 DMF operations ...
    
    async def get_exported_package_url(self, execution_id: str) -> str:
        """Get download URL for exported package."""
        await self._ensure_metadata_initialized()
        return await self.dmf_ops.get_exported_package_url(execution_id)
    
    # ... Continue for all operations ...
```

## MCP Tools Mixin Implementation

### 1. DmfToolsMixin Class

Create new file: `src/d365fo_client/mcp/mixins/dmf_tools_mixin.py`

```python
"""DMF (Data Management Framework) tools mixin for FastMCP server."""

import logging
from typing import Optional

from .base_tools_mixin import BaseToolsMixin

logger = logging.getLogger(__name__)


class DmfToolsMixin(BaseToolsMixin):
    """Data Management Framework tools for FastMCP server.
    
    Provides tools for D365FO data import/export, package management,
    and execution monitoring through the Data Management Framework (DMF).
    """

    def register_dmf_tools(self):
        """Register all DMF tools with FastMCP."""
        
        # ====================================================================
        # EXPORT OPERATIONS
        # ====================================================================
        
        @self.mcp.tool()
        async def d365fo_dmf_export_to_package(
            definition_group_id: str,
            package_name: str,
            execution_id: str = "",
            re_execute: bool = False,
            legal_entity_id: str = "",
            profile: str = "default",
        ) -> dict:
            """Export data to package from D365FO.
            
            Synchronously exports data from D365 Finance & Operations to a data package
            based on a definition group configuration.
            
            Args:
                definition_group_id: Definition group identifier (data project name)
                package_name: Name for the exported package
                execution_id: Existing execution ID for re-execution (optional)
                re_execute: Whether to re-execute an existing export
                legal_entity_id: Legal entity/company code (e.g., 'USMF')
                profile: Profile name for connection configuration
                
            Returns:
                Dictionary with execution ID and export status
                
            Example:
                Export customer data: definition_group_id="CustomerExport",
                package_name="Customers_2025-10-05", legal_entity_id="USMF"
            """
            try:
                client = await self._get_client(profile)
                
                result = await client.export_to_package(
                    definition_group_id=definition_group_id,
                    package_name=package_name,
                    execution_id=execution_id,
                    re_execute=re_execute,
                    legal_entity_id=legal_entity_id,
                )
                
                return {
                    "success": True,
                    "execution_id": result,
                    "definition_group": definition_group_id,
                    "package_name": package_name,
                    "operation": "export_to_package",
                }
                
            except Exception as e:
                logger.error(f"DMF export to package failed: {e}")
                return self._create_error_response(
                    e, "d365fo_dmf_export_to_package", locals()
                )
        
        @self.mcp.tool()
        async def d365fo_dmf_export_to_package_async(
            definition_group_id: str,
            package_name: str,
            execution_id: str = "",
            re_execute: bool = False,
            legal_entity_id: str = "",
            entity_list: str = "",
            profile: str = "default",
        ) -> dict:
            """Export data to package asynchronously from D365FO.
            
            Asynchronously exports data from D365 Finance & Operations. Better for
            large data exports as it returns immediately with an execution ID.
            
            Args:
                definition_group_id: Definition group identifier
                package_name: Name for the exported package
                execution_id: Existing execution ID for re-execution (optional)
                re_execute: Whether to re-execute an existing export
                legal_entity_id: Legal entity/company code
                entity_list: Comma-separated list of entities to export (optional)
                profile: Profile name for connection configuration
                
            Returns:
                Dictionary with execution ID for tracking progress
            """
            try:
                client = await self._get_client(profile)
                
                result = await client.export_to_package_async(
                    definition_group_id=definition_group_id,
                    package_name=package_name,
                    execution_id=execution_id,
                    re_execute=re_execute,
                    legal_entity_id=legal_entity_id,
                    entity_list=entity_list,
                )
                
                return {
                    "success": True,
                    "execution_id": result,
                    "definition_group": definition_group_id,
                    "package_name": package_name,
                    "operation": "export_to_package_async",
                    "note": "Export started asynchronously. Use execution_id to check status.",
                }
                
            except Exception as e:
                logger.error(f"DMF async export failed: {e}")
                return self._create_error_response(
                    e, "d365fo_dmf_export_to_package_async", locals()
                )
        
        @self.mcp.tool()
        async def d365fo_dmf_get_exported_package_url(
            execution_id: str,
            profile: str = "default",
        ) -> dict:
            """Get download URL for exported package.
            
            Retrieves the download URL for a completed export package.
            
            Args:
                execution_id: Execution ID from export operation
                profile: Profile name for connection configuration
                
            Returns:
                Dictionary with download URL and package information
            """
            try:
                client = await self._get_client(profile)
                
                url = await client.get_exported_package_url(execution_id)
                
                return {
                    "success": True,
                    "execution_id": execution_id,
                    "download_url": url,
                    "note": "Use this URL to download the exported package file.",
                }
                
            except Exception as e:
                logger.error(f"Get exported package URL failed: {e}")
                return self._create_error_response(
                    e, "d365fo_dmf_get_exported_package_url", locals()
                )
        
        # ====================================================================
        # IMPORT OPERATIONS
        # ====================================================================
        
        @self.mcp.tool()
        async def d365fo_dmf_import_from_package(
            package_url: str,
            definition_group_id: str,
            execution_id: str = "",
            execute: bool = True,
            overwrite: bool = False,
            legal_entity_id: str = "",
            profile: str = "default",
        ) -> dict:
            """Import data from package into D365FO.
            
            Imports data from a data package into D365 Finance & Operations.
            
            Args:
                package_url: URL to the data package file
                definition_group_id: Definition group identifier
                execution_id: Existing execution ID (optional)
                execute: Whether to execute import immediately (True) or stage only (False)
                overwrite: Whether to overwrite existing data
                legal_entity_id: Target legal entity/company code
                profile: Profile name for connection configuration
                
            Returns:
                Dictionary with execution ID and import status
            """
            try:
                client = await self._get_client(profile)
                
                result = await client.import_from_package(
                    package_url=package_url,
                    definition_group_id=definition_group_id,
                    execution_id=execution_id,
                    execute=execute,
                    overwrite=overwrite,
                    legal_entity_id=legal_entity_id,
                )
                
                return {
                    "success": True,
                    "execution_id": result,
                    "definition_group": definition_group_id,
                    "package_url": package_url,
                    "execute": execute,
                    "operation": "import_from_package",
                }
                
            except Exception as e:
                logger.error(f"DMF import from package failed: {e}")
                return self._create_error_response(
                    e, "d365fo_dmf_import_from_package", locals()
                )
        
        # ====================================================================
        # STATUS & MONITORING
        # ====================================================================
        
        @self.mcp.tool()
        async def d365fo_dmf_get_execution_status(
            execution_id: str,
            profile: str = "default",
        ) -> dict:
            """Get execution status for DMF operation.
            
            Retrieves comprehensive status information for a DMF execution.
            
            Args:
                execution_id: Execution ID to check
                profile: Profile name for connection configuration
                
            Returns:
                Dictionary with detailed execution status
            """
            try:
                client = await self._get_client(profile)
                
                status = await client.get_execution_summary_status(execution_id)
                
                return {
                    "success": True,
                    "execution_id": execution_id,
                    "status": status,
                }
                
            except Exception as e:
                logger.error(f"Get execution status failed: {e}")
                return self._create_error_response(
                    e, "d365fo_dmf_get_execution_status", locals()
                )
        
        @self.mcp.tool()
        async def d365fo_dmf_get_execution_errors(
            execution_id: str,
            profile: str = "default",
        ) -> dict:
            """Get error details for DMF execution.
            
            Retrieves detailed error information for failed or partially failed executions.
            
            Args:
                execution_id: Execution ID to check
                profile: Profile name for connection configuration
                
            Returns:
                Dictionary with error details
            """
            try:
                client = await self._get_client(profile)
                
                errors = await client.get_execution_errors(execution_id)
                
                return {
                    "success": True,
                    "execution_id": execution_id,
                    "errors": errors,
                }
                
            except Exception as e:
                logger.error(f"Get execution errors failed: {e}")
                return self._create_error_response(
                    e, "d365fo_dmf_get_execution_errors", locals()
                )
        
        # ====================================================================
        # UTILITY OPERATIONS
        # ====================================================================
        
        @self.mcp.tool()
        async def d365fo_dmf_get_azure_write_url(
            unique_file_name: str,
            profile: str = "default",
        ) -> dict:
            """Get Azure Blob Storage write URL for package upload.
            
            Generates a temporary Azure Blob Storage URL with SAS token
            for uploading data packages.
            
            Args:
                unique_file_name: Unique file name for the package
                profile: Profile name for connection configuration
                
            Returns:
                Dictionary with Azure write URL and SAS token
            """
            try:
                client = await self._get_client(profile)
                
                url = await client.get_azure_write_url(unique_file_name)
                
                return {
                    "success": True,
                    "file_name": unique_file_name,
                    "write_url": url,
                    "note": "Use HTTP PUT to upload file to this URL.",
                }
                
            except Exception as e:
                logger.error(f"Get Azure write URL failed: {e}")
                return self._create_error_response(
                    e, "d365fo_dmf_get_azure_write_url", locals()
                )
        
        logger.info("DMF tools registered successfully")
```

### 2. Update Mixin Exports

Update `src/d365fo_client/mcp/mixins/__init__.py`:

```python
"""MCP tools mixins for modular tool organization."""

from .base_tools_mixin import BaseToolsMixin
from .connection_tools_mixin import ConnectionToolsMixin
from .crud_tools_mixin import CrudToolsMixin
from .database_tools_mixin import DatabaseToolsMixin
from .dmf_tools_mixin import DmfToolsMixin  # NEW
from .label_tools_mixin import LabelToolsMixin
from .metadata_tools_mixin import MetadataToolsMixin
from .performance_tools_mixin import PerformanceToolsMixin
from .profile_tools_mixin import ProfileToolsMixin
from .sync_tools_mixin import SyncToolsMixin

__all__ = [
    "BaseToolsMixin",
    "ConnectionToolsMixin",
    "CrudToolsMixin",
    "DatabaseToolsMixin",
    "DmfToolsMixin",  # NEW
    "LabelToolsMixin",
    "MetadataToolsMixin",
    "PerformanceToolsMixin",
    "ProfileToolsMixin",
    "SyncToolsMixin",
]
```

### 3. Update FastMCP Server

Update `src/d365fo_client/mcp/fastmcp_server.py`:

```python
# Add to imports
from .mixins import (
    ConnectionToolsMixin,
    CrudToolsMixin,
    DatabaseToolsMixin,
    DmfToolsMixin,  # NEW
    LabelToolsMixin,
    MetadataToolsMixin,
    PerformanceToolsMixin,
    ProfileToolsMixin,
    SyncToolsMixin,
)

# Update class definition
class FastD365FOMCPServer(
    DatabaseToolsMixin,
    MetadataToolsMixin,
    CrudToolsMixin,
    DmfToolsMixin,  # NEW - Add to inheritance chain
    ProfileToolsMixin,
    SyncToolsMixin,
    LabelToolsMixin,
    ConnectionToolsMixin,
    PerformanceToolsMixin,
):
    """FastMCP-based D365FO MCP Server with multi-transport support."""
    
    # In _register_tools method, add:
    def _register_tools(self):
        """Register all tools using mixins."""
        logger.info("Registering tools from mixins...")
        
        self.register_database_tools()
        self.register_metadata_tools()
        self.register_crud_tools()
        self.register_dmf_tools()  # NEW
        self.register_profile_tools()
        self.register_sync_tools()
        self.register_label_tools()
        self.register_connection_tools()
        self.register_performance_tools()
        
        logger.info("All tools registered successfully")
```

## Data Models

Add to `src/d365fo_client/models.py`:

```python
@dataclass
class DMFExecutionStatus:
    """DMF execution status information"""
    
    execution_id: str
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_records: int = 0
    processed_records: int = 0
    failed_records: int = 0
    error_message: Optional[str] = None


@dataclass
class DMFExportOptions:
    """Options for DMF export operations"""
    
    definition_group_id: str
    package_name: str
    execution_id: str = ""
    re_execute: bool = False
    legal_entity_id: str = ""
    entity_list: str = ""
    export_preview_count: int = 0


@dataclass
class DMFImportOptions:
    """Options for DMF import operations"""
    
    package_url: str
    definition_group_id: str
    execution_id: str = ""
    execute: bool = True
    overwrite: bool = False
    legal_entity_id: str = ""
    import_batch_group_id: str = ""
    fail_on_error: bool = False


@dataclass
class DMFExecutionSummary:
    """Summary information for DMF execution"""
    
    execution_id: str
    definition_group_id: str
    operation_type: str  # "Export" or "Import"
    status: str
    entity_statuses: List[Dict[str, Any]] = field(default_factory=list)
    total_entities: int = 0
    completed_entities: int = 0
    failed_entities: int = 0
```

## Error Handling

Add to `src/d365fo_client/exceptions.py`:

```python
class DMFError(FOClientError):
    """Exception raised for DMF-specific errors"""
    
    def __init__(
        self,
        message: str,
        execution_id: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.execution_id = execution_id
        self.error_details = error_details or {}


class DMFExecutionError(DMFError):
    """Exception raised when DMF execution fails"""
    pass


class DMFPackageError(DMFError):
    """Exception raised for package-related errors"""
    pass


class DMFTimeoutError(DMFError):
    """Exception raised when DMF operation times out"""
    pass
```

## Testing Strategy

### 1. Unit Tests

Create `tests/unit/test_dmf_operations.py`:

```python
"""Unit tests for DMF operations."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from d365fo_client.dmf_operations import DmfOperations
from d365fo_client.exceptions import DMFError


@pytest.fixture
def dmf_ops():
    """Create DmfOperations instance with mocked session manager."""
    session_manager = MagicMock()
    base_url = "https://test.dynamics.com"
    return DmfOperations(session_manager, base_url)


@pytest.mark.asyncio
async def test_export_to_package(dmf_ops):
    """Test export_to_package operation."""
    # Setup mock
    mock_session = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value="EXEC-12345")
    mock_session.post.return_value.__aenter__.return_value = mock_response
    dmf_ops.session_manager.get_session = AsyncMock(return_value=mock_session)
    
    # Execute
    result = await dmf_ops.export_to_package(
        definition_group_id="TestGroup",
        package_name="TestPackage",
    )
    
    # Assert
    assert result == "EXEC-12345"
    mock_session.post.assert_called_once()


# Add more unit tests for all 25 operations...
```

### 2. Integration Tests

Create `tests/integration/test_dmf_integration.py`:

```python
"""Integration tests for DMF operations."""

import pytest
import os

from d365fo_client import FOClient, FOClientConfig


@pytest.fixture
async def client():
    """Create FOClient for integration testing."""
    config = FOClientConfig(
        base_url=os.getenv("D365FO_BASE_URL"),
        credential_source=None,
    )
    async with FOClient(config) as client:
        yield client


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dmf_initialize(client):
    """Test DMF initialization."""
    await client.initialize_data_management_async()
    # Verify no errors raised


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dmf_export_flow(client):
    """Test complete export flow."""
    # 1. Export data
    execution_id = await client.export_to_package_async(
        definition_group_id="TestGroup",
        package_name="IntegrationTest",
        legal_entity_id="USMF",
    )
    
    assert execution_id
    
    # 2. Check status
    status = await client.get_execution_summary_status(execution_id)
    assert status is not None
    
    # 3. Get package URL (when complete)
    # url = await client.get_exported_package_url(execution_id)
    # assert url


# Add more integration tests...
```

## Documentation Requirements

### 1. API Documentation

Add comprehensive docstrings to all methods following the project's existing patterns (Google-style docstrings).

### 2. Usage Examples

Create `examples/dmf_operations_example.py`:

```python
"""Examples of using DMF operations with d365fo-client."""

import asyncio
import os
from d365fo_client import FOClient, FOClientConfig


async def export_example():
    """Example: Export data to package."""
    config = FOClientConfig(
        base_url=os.getenv("D365FO_BASE_URL"),
        credential_source=None,
    )
    
    async with FOClient(config) as client:
        # Export data asynchronously
        execution_id = await client.export_to_package_async(
            definition_group_id="CustomerMasterData",
            package_name="Customers_2025-10-05",
            legal_entity_id="USMF",
        )
        
        print(f"Export started: {execution_id}")
        
        # Check status
        status = await client.get_execution_summary_status(execution_id)
        print(f"Status: {status}")
        
        # Get download URL (when complete)
        # url = await client.get_exported_package_url(execution_id)
        # print(f"Download: {url}")


async def import_example():
    """Example: Import data from package."""
    config = FOClientConfig(
        base_url=os.getenv("D365FO_BASE_URL"),
        credential_source=None,
    )
    
    async with FOClient(config) as client:
        # Import data
        execution_id = await client.import_from_package(
            package_url="https://storage.example.com/package.zip",
            definition_group_id="CustomerMasterData",
            execute=True,
            legal_entity_id="USMF",
        )
        
        print(f"Import started: {execution_id}")


if __name__ == "__main__":
    asyncio.run(export_example())
    asyncio.run(import_example())
```

### 3. README Updates

Update main README.md with DMF operations section:

```markdown
## Data Management Framework (DMF) Operations

The d365fo-client provides comprehensive support for D365 F&O Data Management Framework operations:

### Export Operations
- Export data to packages (sync/async)
- Export with preview/sampling
- Delta exports (only changed data)
- Download exported packages

### Import Operations  
- Import from data packages
- Import from DMT packages
- Staging and validation

### Status & Monitoring
- Check execution status
- Monitor entity-level progress
- Retrieve error details

### Example Usage
\```python
async with FOClient(config) as client:
    # Export data
    execution_id = await client.export_to_package_async(
        definition_group_id="CustomerData",
        package_name="Customers_Export",
        legal_entity_id="USMF"
    )
    
    # Check status
    status = await client.get_execution_summary_status(execution_id)
    
    # Download package
    url = await client.get_exported_package_url(execution_id)
\```

See [examples/dmf_operations_example.py](examples/dmf_operations_example.py) for more examples.
```

## Implementation Checklist

### Phase 1: Core Implementation
- [ ] Create `dmf_operations.py` with all 25 operations
- [ ] Add DMF data models to `models.py`
- [ ] Add DMF exceptions to `exceptions.py`
- [ ] Integrate DmfOperations into FOClient
- [ ] Add unit tests for all operations

### Phase 2: MCP Integration  
- [ ] Create `dmf_tools_mixin.py` with MCP tools
- [ ] Update mixin exports in `__init__.py`
- [ ] Integrate DmfToolsMixin into FastD365FOMCPServer
- [ ] Add MCP tool tests

### Phase 3: Documentation & Examples
- [ ] Add comprehensive docstrings
- [ ] Create usage examples
- [ ] Update README.md
- [ ] Create MCP demo script
- [ ] Add integration tests

### Phase 4: Testing & Validation
- [ ] Run unit tests
- [ ] Run integration tests (sandbox environment)
- [ ] Validate MCP tool registration
- [ ] Performance testing
- [ ] Code review

## Success Criteria

1. ✅ All 25 DMF actions implemented in FOClient
2. ✅ Full type safety with proper type hints
3. ✅ Comprehensive error handling with DMF-specific exceptions
4. ✅ MCP tools mixin created and integrated
5. ✅ Unit test coverage >90%
6. ✅ Integration tests pass in sandbox environment
7. ✅ Complete documentation and examples
8. ✅ Code follows project conventions and patterns

## Notes for Implementation

### Key Design Decisions

1. **Separate Operations Class**: Following the pattern of `CrudOperations`, `MetadataAPIOperations`, etc.

2. **All Actions BoundToEntitySet**: All 25 actions operate on the `DataManagementDefinitionGroups` collection, so URL construction is consistent.

3. **Async-First**: All operations are async to match project patterns.

4. **Error Context**: DMF errors include execution_id and error_details for better debugging.

5. **MCP Tool Subset**: Initially expose the most common operations (export, import, status) as MCP tools. Additional tools can be added based on usage.

6. **Type Safety**: Use dataclasses for structured data (options, status, summaries).

### API Design Principles

1. **Consistency**: Follow existing FOClient method naming and parameter patterns
2. **Explicit Parameters**: Use explicit parameters instead of options objects for better IDE support
3. **Sensible Defaults**: Provide defaults for optional parameters
4. **Documentation**: Every method has comprehensive docstrings with examples
5. **Error Messages**: Clear, actionable error messages with context

### Testing Approach

1. **Unit Tests**: Mock all HTTP calls, test logic and error handling
2. **Integration Tests**: Test against sandbox environment with real DMF operations
3. **MCP Tests**: Validate tool registration and execution
4. **Performance Tests**: Ensure operations complete within reasonable timeframes

## References

- [D365 F&O Data Management Framework Documentation](https://learn.microsoft.com/en-us/dynamics365/fin-ops-core/dev-itpro/data-entities/data-entities-data-packages)
- [OData Action Specification](https://www.odata.org/documentation/)
- Existing implementation patterns in `crud.py`, `metadata_api.py`
- MCP tool patterns in `crud_tools_mixin.py`, `metadata_tools_mixin.py`

## Appendix: Complete Action Reference

### Export Actions
1. `ExportToPackage` - Synchronous export
2. `ExportToPackageAsync` - Asynchronous export
3. `ExportToPackagePreview` - Export with preview
4. `ExportToPackagePreviewAsync` - Async export with preview
5. `ExportToPackageDelta` - Delta export (only changes)
6. `ExportFromPackage` - Export using template
7. `GetExportedPackageUrl` - Get download URL

### Import Actions
8. `ImportFromPackage` - Standard import
9. `ImportFromDMTPackage` - DMT package import

### Initialization Actions
10. `InitializeDataManagement` - Sync initialization
11. `InitializeDataManagementAsync` - Async initialization

### Status & Monitoring Actions
12. `GetExecutionSummaryStatus` - Overall status
13. `GetEntityExecutionSummaryStatusList` - Entity statuses
14. `GetMessageStatus` - Message queue status

### Error Management Actions
15. `GetExecutionErrors` - Error details
16. `GetImportTargetErrorKeysFileUrl` - Target error URL
17. `GetImportStagingErrorFileUrl` - Staging error URL
18. `GenerateImportTargetErrorKeysFile` - Generate error file

### Utility Actions
19. `GetAzureWriteUrl` - Azure upload URL
20. `GetEntitySequence` - Execution sequence
21. `ResetVersionToken` - Reset change tracking
22. `GetExecutionIdByMessageId` - Message to execution mapping

### Reserved (3 actions for future categories)
23-25. Reserved for future expansion

---

**End of Specification Document**
