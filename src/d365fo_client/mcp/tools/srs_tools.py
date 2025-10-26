"""SRS Report download tools for MCP server."""

import json
import logging
from pathlib import Path
from typing import List

from mcp import Tool
from mcp.types import TextContent

from ..client_manager import D365FOClientManager

logger = logging.getLogger(__name__)


class SrsTools:
    """SRS Report download tools for the MCP server."""

    def __init__(self, client_manager: D365FOClientManager):
        """Initialize SRS tools.

        Args:
            client_manager: D365FO client manager instance
        """
        self.client_manager = client_manager

    def get_tools(self) -> List[Tool]:
        """Get list of SRS report tools.

        Returns:
            List of Tool definitions
        """
        return [
            self._get_download_srs_report_tool(),
            self._get_download_customer_invoice_tool(),
            self._get_download_free_text_invoice_tool(),
        ]

    def _get_download_srs_report_tool(self) -> Tool:
        """Get download SRS report tool definition."""
        return Tool(
            name="d365fo_download_srs_report",
            description="Download SQL Server Reporting Services (SSRS/SRS) reports from D365 Finance & Operations as PDF files. This tool generates and downloads business documents like invoices, purchase orders, confirmations, and other reports by calling the D365FO SRS reporting engine. The report is returned as a PDF file saved to a specified location. Supports various document types through different controller configurations. Use this for programmatic report generation and archival.",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "string",
                        "description": "The unique identifier/key of the document to generate the report for. This is the primary key value from the source table (e.g., invoice number 'CIV-000708', order ID 'SO-001234'). The document must exist in the D365FO database for the specified legal entity.",
                    },
                    "legal_entity": {
                        "type": "string",
                        "description": "The legal entity/company code (DataAreaId) where the document exists. Examples: 'USMF', 'DEMF', 'FRRT'. This must match the company context where the document was created in D365FO.",
                    },
                    "controller_name": {
                        "type": "string",
                        "description": "The SSRS controller class name that defines which report to generate. Common controllers: 'SalesInvoiceController' (customer invoices), 'FreeTextInvoiceController' (free text invoices), 'CustDebitCreditNoteController' (debit/credit notes), 'SalesConfirmController' (sales confirmations), 'PurchPurchaseOrderController' (purchase orders). Each controller is linked to a specific report design and business logic.",
                        "default": "SalesInvoiceController",
                    },
                    "data_table": {
                        "type": "string",
                        "description": "The database table name that contains the document record. Must match the controller's expected table. Common tables: 'CustInvoiceJour' (customer invoices), 'CustConfirmJour' (sales confirmations), 'VendPurchOrderJour' (purchase orders). This tells the reporting engine where to look for the document data.",
                        "default": "CustInvoiceJour",
                    },
                    "data_field": {
                        "type": "string",
                        "description": "The field name in the data table that stores the document ID. This is used to locate the specific record. Common fields: 'InvoiceId' (invoices), 'ConfirmId' (confirmations), 'SalesId' (sales orders), 'PurchId' (purchase orders). Must be the exact field name as defined in the table schema.",
                        "default": "InvoiceId",
                    },
                    "document_type": {
                        "type": "string",
                        "description": "Human-readable document type identifier used for filename generation and logging. Examples: 'CustomerInvoice', 'FreeTextInvoice', 'PurchaseOrder', 'SalesConfirmation'. This helps organize saved files and makes them easier to identify.",
                        "default": "SalesInvoice",
                    },
                    "save_path": {
                        "type": "string",
                        "description": "Full absolute path where the PDF file should be saved (optional). If provided, must be a valid writable file path including the .pdf extension. If not provided, the file will be saved in './Reports/' directory with an auto-generated filename containing the document type, ID, legal entity, and timestamp. Parent directories will be created if they don't exist. Use MCP roots to get appropriate save locations.",
                    },
                    "profile": {
                        "type": "string",
                        "description": "Configuration profile name for D365FO connection settings. Use 'default' for the primary environment or specify a different profile for multi-environment scenarios (dev, test, prod).",
                        "default": "default",
                    },
                },
                "required": ["document_id", "legal_entity"],
            },
        )

    def _get_download_customer_invoice_tool(self) -> Tool:
        """Get download customer invoice tool definition (convenience tool)."""
        return Tool(
            name="d365fo_download_customer_invoice",
            description="Download a customer invoice report as PDF from D365 Finance & Operations. This is a convenience tool that wraps the generic SRS download functionality with preset configurations for customer invoices (CustInvoiceJour table, SalesInvoiceController). Use this when you need to quickly download customer invoices without specifying all the technical parameters. The invoice must exist in the specified legal entity.",
            inputSchema={
                "type": "object",
                "properties": {
                    "invoice_id": {
                        "type": "string",
                        "description": "The customer invoice number/ID to download (e.g., 'CIV-000708', 'INV-2024-001'). This is the InvoiceId field value from the CustInvoiceJour table in D365FO.",
                    },
                    "legal_entity": {
                        "type": "string",
                        "description": "The legal entity/company code (DataAreaId) where the invoice exists. Examples: 'USMF', 'DEMF', 'FRRT'.",
                    },
                    "save_path": {
                        "type": "string",
                        "description": "Full absolute path where the PDF should be saved (optional). If not provided, saves to './Reports/' with auto-generated filename. Use MCP roots to get appropriate save locations.",
                    },
                    "profile": {
                        "type": "string",
                        "description": "Configuration profile name (optional - uses default profile if not specified)",
                        "default": "default",
                    },
                },
                "required": ["invoice_id", "legal_entity"],
            },
        )

    def _get_download_free_text_invoice_tool(self) -> Tool:
        """Get download free text invoice tool definition (convenience tool)."""
        return Tool(
            name="d365fo_download_free_text_invoice",
            description="Download a free text invoice report as PDF from D365 Finance & Operations. This is a convenience tool specifically configured for free text invoices using the FreeTextInvoiceController. Free text invoices are customer invoices that don't originate from sales orders. The invoice must exist in the specified legal entity.",
            inputSchema={
                "type": "object",
                "properties": {
                    "invoice_id": {
                        "type": "string",
                        "description": "The free text invoice number/ID to download (e.g., 'FTI-00000021', 'FTI-2024-001'). This is the InvoiceId field value from the CustInvoiceJour table where the invoice was created as a free text invoice.",
                    },
                    "legal_entity": {
                        "type": "string",
                        "description": "The legal entity/company code (DataAreaId) where the invoice exists. Examples: 'USMF', 'DEMF', 'FRRT'.",
                    },
                    "save_path": {
                        "type": "string",
                        "description": "Full absolute path where the PDF should be saved (optional). If not provided, saves to './Reports/' with auto-generated filename. Use MCP roots to get appropriate save locations.",
                    },
                    "profile": {
                        "type": "string",
                        "description": "Configuration profile name (optional - uses default profile if not specified)",
                        "default": "default",
                    },
                },
                "required": ["invoice_id", "legal_entity"],
            },
        )

    async def execute_download_srs_report(self, arguments: dict) -> List[TextContent]:
        """Execute download SRS report tool.

        Args:
            arguments: Tool arguments

        Returns:
            List of TextContent responses
        """
        try:
            profile = arguments.get("profile", "default")
            client = await self.client_manager.get_client(profile)

            # Download the report
            saved_path = await client.download_srs_report(
                document_id=arguments["document_id"],
                legal_entity=arguments["legal_entity"],
                controller_name=arguments.get(
                    "controller_name", "SalesInvoiceController"
                ),
                data_table=arguments.get("data_table", "CustInvoiceJour"),
                data_field=arguments.get("data_field", "InvoiceId"),
                document_type=arguments.get("document_type", "SalesInvoice"),
                save_path=arguments.get("save_path"),
            )

            response = {
                "success": True,
                "document_id": arguments["document_id"],
                "legal_entity": arguments["legal_entity"],
                "saved_path": saved_path,
                "file_size_bytes": Path(saved_path).stat().st_size,
                "message": f"SRS report downloaded successfully to: {saved_path}",
            }

            return [TextContent(type="text", text=json.dumps(response, indent=2))]

        except Exception as e:
            logger.error(f"Download SRS report failed: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "tool": "d365fo_download_srs_report",
                "document_id": arguments.get("document_id"),
                "legal_entity": arguments.get("legal_entity"),
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]

    async def execute_download_customer_invoice(
        self, arguments: dict
    ) -> List[TextContent]:
        """Execute download customer invoice tool.

        Args:
            arguments: Tool arguments

        Returns:
            List of TextContent responses
        """
        try:
            profile = arguments.get("profile", "default")
            client = await self.client_manager.get_client(profile)

            # Download customer invoice with preset configuration
            saved_path = await client.download_srs_report(
                document_id=arguments["invoice_id"],
                legal_entity=arguments["legal_entity"],
                controller_name="SalesInvoiceController",
                data_table="CustInvoiceJour",
                data_field="InvoiceId",
                document_type="CustomerInvoice",
                save_path=arguments.get("save_path"),
            )

            response = {
                "success": True,
                "invoice_id": arguments["invoice_id"],
                "legal_entity": arguments["legal_entity"],
                "saved_path": saved_path,
                "file_size_bytes": Path(saved_path).stat().st_size,
                "message": f"Customer invoice downloaded successfully to: {saved_path}",
            }

            return [TextContent(type="text", text=json.dumps(response, indent=2))]

        except Exception as e:
            logger.error(f"Download customer invoice failed: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "tool": "d365fo_download_customer_invoice",
                "invoice_id": arguments.get("invoice_id"),
                "legal_entity": arguments.get("legal_entity"),
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]

    async def execute_download_free_text_invoice(
        self, arguments: dict
    ) -> List[TextContent]:
        """Execute download free text invoice tool.

        Args:
            arguments: Tool arguments

        Returns:
            List of TextContent responses
        """
        try:
            profile = arguments.get("profile", "default")
            client = await self.client_manager.get_client(profile)

            # Download free text invoice with preset configuration
            saved_path = await client.download_srs_report(
                document_id=arguments["invoice_id"],
                legal_entity=arguments["legal_entity"],
                controller_name="FreeTextInvoiceController",
                data_table="CustInvoiceJour",
                data_field="InvoiceId",
                document_type="FreeTextInvoice",
                save_path=arguments.get("save_path"),
            )

            response = {
                "success": True,
                "invoice_id": arguments["invoice_id"],
                "legal_entity": arguments["legal_entity"],
                "saved_path": saved_path,
                "file_size_bytes": Path(saved_path).stat().st_size,
                "message": f"Free text invoice downloaded successfully to: {saved_path}",
            }

            return [TextContent(type="text", text=json.dumps(response, indent=2))]

        except Exception as e:
            logger.error(f"Download free text invoice failed: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "tool": "d365fo_download_free_text_invoice",
                "invoice_id": arguments.get("invoice_id"),
                "legal_entity": arguments.get("legal_entity"),
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
