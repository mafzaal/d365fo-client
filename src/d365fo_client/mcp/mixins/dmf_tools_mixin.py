"""DMF (Data Management Framework) tools mixin for FastMCP server."""

import logging

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
