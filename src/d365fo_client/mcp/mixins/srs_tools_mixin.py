"""SRS Tools Mixin for FastMCP server."""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SrsToolsMixin:
    """Mixin providing SRS report download tools for FastMCP server."""

    def setup_srs_tools(self):
        """Setup SRS tools configuration."""
        # No specific setup needed for SRS tools
        pass

    def register_srs_tools(self):
        """Register SRS report download tools."""

        @self.mcp.tool()
        async def d365fo_download_srs_report(
            document_id: str,
            legal_entity: str,
            controller_name: str = "SalesInvoiceController",
            data_table: str = "CustInvoiceJour",
            data_field: str = "InvoiceId",
            document_type: str = "SalesInvoice",
            save_path: str = None,
            profile: str = "default",
        ) -> dict[str, Any]:
            """Download SQL Server Reporting Services (SSRS/SRS) reports from D365 Finance & Operations as PDF files.

            This tool generates and downloads business documents like invoices, purchase orders, confirmations,
            and other reports by calling the D365FO SRS reporting engine. The report is returned as a PDF file
            saved to a specified location.

            Args:
                document_id: The unique identifier/key of the document (e.g., 'CIV-000708', 'SO-001234')
                legal_entity: The legal entity/company code (DataAreaId) where the document exists (e.g., 'USMF')
                controller_name: The SSRS controller class name (default: 'SalesInvoiceController')
                    Common controllers:
                    - SalesInvoiceController: Customer invoices
                    - FreeTextInvoiceController: Free text invoices
                    - CustDebitCreditNoteController: Debit/credit notes
                    - SalesConfirmController: Sales confirmations
                    - PurchPurchaseOrderController: Purchase orders
                data_table: The database table containing the document (default: 'CustInvoiceJour')
                data_field: The field name that stores the document ID (default: 'InvoiceId')
                document_type: Human-readable document type for filename (default: 'SalesInvoice')
                save_path: Full path where PDF should be saved (optional, auto-generates if not provided)
                profile: Configuration profile name (default: 'default')

            Common controller/table/field combinations:
                | Controller | Table | Field Name | Field Type | Document Type |
                |-----------|-------|-----------|------------|---------------|
                | `SalesInvoiceController` | `CustInvoiceJour` | `InvoiceId` | Invoice ID | Sales Invoice |
                | `FreeTextInvoiceController` | `CustInvoiceJour` | `InvoiceId` | Invoice ID | Free Text Invoice |
                | `CustDebitCreditNoteController` | `CustInvoiceJour` | `InvoiceId` | Invoice ID | Debit/Credit Note |
                | `SalesConfirmController` | `CustConfirmJour` | `ConfirmId` or `SalesId` | Confirm/Sales ID | Sales Confirmation |
                | `PurchPurchaseOrderController` | `VendPurchOrderJour` | `PurchId` | Purchase Order ID | Purchase Order |
            Returns:
                Dictionary with download result including saved file path
            """
            try:
                client = await self.client_manager.get_client(profile)

                # Download the report
                saved_path = await client.download_srs_report(
                    document_id=document_id,
                    legal_entity=legal_entity,
                    controller_name=controller_name,
                    data_table=data_table,
                    data_field=data_field,
                    document_type=document_type,
                    save_path=save_path,
                )

                return {
                    "success": True,
                    "document_id": document_id,
                    "legal_entity": legal_entity,
                    "saved_path": saved_path,
                    "file_size_bytes": Path(saved_path).stat().st_size,
                    "message": f"SRS report downloaded successfully to: {saved_path}",
                }

            except Exception as e:
                logger.error(f"Download SRS report failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "tool": "d365fo_download_srs_report",
                    "document_id": document_id,
                    "legal_entity": legal_entity,
                }

        @self.mcp.tool()
        async def d365fo_download_customer_invoice(
            invoice_id: str,
            legal_entity: str,
            save_path: str = None,
            profile: str = "default",
        ) -> dict[str, Any]:
            """Download a customer invoice report as PDF from D365 Finance & Operations.

            This is a convenience tool with preset configurations for customer invoices.
            Use this when you need to quickly download customer invoices without specifying
            all the technical parameters.

            To find available invoices to download, query the Customer Invoice Journal entity:
            - Entity name: CustInvoiceJourBiEntity
            - Collection name: CustInvoiceJourBiEntities
            - Key fields: InvoiceId, InvoiceDate, InvoiceAccount, InvoiceAmount, SalesType, dataAreaId
            - Use d365fo_query_entities tool to search for invoices

            Example query to find invoices:
                d365fo_query_entities(
                    entityName="CustInvoiceJourBiEntities",
                    filter="InvoiceDate ge 2024-01-01",
                    select=["InvoiceId", "InvoiceDate", "InvoiceAccount", "InvoiceAmount", "SalesType"]
                )

            Args:
                invoice_id: The customer invoice number/ID (e.g., 'CIV-000708', 'INV-2024-001')
                legal_entity: The legal entity/company code (e.g., 'USMF', 'DEMF')
                save_path: Full path where PDF should be saved (optional, auto-generates if not provided)
                profile: Configuration profile name (default: 'default')

            Returns:
                Dictionary with download result including saved file path
            """
            try:
                client = await self.client_manager.get_client(profile)

                # Download customer invoice with preset configuration
                saved_path = await client.download_srs_report(
                    document_id=invoice_id,
                    legal_entity=legal_entity,
                    controller_name="SalesInvoiceController",
                    data_table="CustInvoiceJour",
                    data_field="InvoiceId",
                    document_type="CustomerInvoice",
                    save_path=save_path,
                )

                return {
                    "success": True,
                    "invoice_id": invoice_id,
                    "legal_entity": legal_entity,
                    "saved_path": saved_path,
                    "file_size_bytes": Path(saved_path).stat().st_size,
                    "message": f"Customer invoice downloaded successfully to: {saved_path}",
                }

            except Exception as e:
                logger.error(f"Download customer invoice failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "tool": "d365fo_download_customer_invoice",
                    "invoice_id": invoice_id,
                    "legal_entity": legal_entity,
                }

        @self.mcp.tool()
        async def d365fo_download_free_text_invoice(
            invoice_id: str,
            legal_entity: str,
            save_path: str = None,
            profile: str = "default",
        ) -> dict[str, Any]:
            """Download a free text invoice report as PDF from D365 Finance & Operations.

            This is a convenience tool specifically configured for free text invoices using
            the FreeTextInvoiceController. Free text invoices are customer invoices that
            don't originate from sales orders.

            To find available invoices to download, query the Customer Invoice Journal entity:
            - Entity name: CustInvoiceJourBiEntity
            - Collection name: CustInvoiceJourBiEntities
            - Key fields: InvoiceId, InvoiceDate, InvoiceAccount, InvoiceAmount, SalesType, dataAreaId
            - Use d365fo_query_entities tool to search for invoices

            Example query to find free text invoices:
                d365fo_query_entities(
                    entityName="CustInvoiceJourBiEntities",
                    filter="InvoiceDate ge 2024-01-01",
                    select=["InvoiceId", "InvoiceDate", "InvoiceAccount", "InvoiceAmount", "SalesType"]
                )

            Args:
                invoice_id: The free text invoice number/ID (e.g., 'FTI-00000021', 'FTI-2024-001')
                legal_entity: The legal entity/company code (e.g., 'USMF', 'DEMF')
                save_path: Full path where PDF should be saved (optional, auto-generates if not provided)
                profile: Configuration profile name (default: 'default')

            Returns:
                Dictionary with download result including saved file path
            """
            try:
                client = await self.client_manager.get_client(profile)

                # Download free text invoice with preset configuration
                saved_path = await client.download_srs_report(
                    document_id=invoice_id,
                    legal_entity=legal_entity,
                    controller_name="FreeTextInvoiceController",
                    data_table="CustInvoiceJour",
                    data_field="InvoiceId",
                    document_type="FreeTextInvoice",
                    save_path=save_path,
                )

                return {
                    "success": True,
                    "invoice_id": invoice_id,
                    "legal_entity": legal_entity,
                    "saved_path": saved_path,
                    "file_size_bytes": Path(saved_path).stat().st_size,
                    "message": f"Free text invoice downloaded successfully to: {saved_path}",
                }

            except Exception as e:
                logger.error(f"Download free text invoice failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "tool": "d365fo_download_free_text_invoice",
                    "invoice_id": invoice_id,
                    "legal_entity": legal_entity,
                }

        @self.mcp.tool()
        async def d365fo_download_debit_credit_note(
            invoice_id: str,
            legal_entity: str,
            save_path: str = None,
            profile: str = "default",
        ) -> dict[str, Any]:
            """Download a debit/credit note report as PDF from D365 Finance & Operations.

            This is a convenience tool specifically configured for debit and credit notes using
            the CustDebitCreditNoteController. These are adjustment documents for customer invoices.

            To find available documents to download, query the Customer Invoice Journal entity:
            - Entity name: CustInvoiceJourBiEntity
            - Collection name: CustInvoiceJourBiEntities
            - Key fields: InvoiceId, InvoiceDate, InvoiceAccount, InvoiceAmount, SalesType, dataAreaId
            - Use d365fo_query_entities tool to search for invoices

            Example query to find invoices:
                d365fo_query_entities(
                    entityName="CustInvoiceJourBiEntities",
                    filter="InvoiceDate ge 2024-01-01",
                    select=["InvoiceId", "InvoiceDate", "InvoiceAccount", "InvoiceAmount", "SalesType"]
                )

            Args:
                invoice_id: The debit/credit note invoice ID (e.g., 'DN-000123', 'CN-000456')
                legal_entity: The legal entity/company code (e.g., 'USMF', 'DEMF')
                save_path: Full path where PDF should be saved (optional, auto-generates if not provided)
                profile: Configuration profile name (default: 'default')

            Returns:
                Dictionary with download result including saved file path
            """
            try:
                client = await self.client_manager.get_client(profile)

                # Download debit/credit note with preset configuration
                saved_path = await client.download_srs_report(
                    document_id=invoice_id,
                    legal_entity=legal_entity,
                    controller_name="CustDebitCreditNoteController",
                    data_table="CustInvoiceJour",
                    data_field="InvoiceId",
                    document_type="DebitCreditNote",
                    save_path=save_path,
                )

                return {
                    "success": True,
                    "invoice_id": invoice_id,
                    "legal_entity": legal_entity,
                    "saved_path": saved_path,
                    "file_size_bytes": Path(saved_path).stat().st_size,
                    "message": f"Debit/credit note downloaded successfully to: {saved_path}",
                }

            except Exception as e:
                logger.error(f"Download debit/credit note failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "tool": "d365fo_download_debit_credit_note",
                    "invoice_id": invoice_id,
                    "legal_entity": legal_entity,
                }

        @self.mcp.tool()
        async def d365fo_download_sales_confirmation(
            confirmation_id: str,
            legal_entity: str,
            save_path: str = None,
            profile: str = "default",
        ) -> dict[str, Any]:
            """Download a sales confirmation report as PDF from D365 Finance & Operations.

            This is a convenience tool specifically configured for sales order confirmations using
            the SalesConfirmController. Sales confirmations are documents sent to customers to confirm
            sales orders.

            To find available confirmations to download, query the Sales Order Confirmation Headers entity:
            - Entity name: SalesOrderConfirmationHeaderEntity
            - Collection name: SalesOrderConfirmationHeaders
            - Key fields: ConfirmationNumber, SalesOrderNumber, ConfirmationDate, OrderingCustomerAccountNumber, TotalConfirmedAmount, dataAreaId
            - Use d365fo_query_entities tool to search for confirmations

            Example query to find confirmations:
                d365fo_query_entities(
                    entityName="SalesOrderConfirmationHeaders",
                    filter="ConfirmationDate ge 2024-01-01",
                    select=["ConfirmationNumber", "SalesOrderNumber", "ConfirmationDate", "OrderingCustomerAccountNumber", "TotalConfirmedAmount"]
                )

            Args:
                confirmation_id: The confirmation ID or sales order ID (e.g., 'SC-000123', 'SO-001234')
                legal_entity: The legal entity/company code (e.g., 'USMF', 'DEMF')
                save_path: Full path where PDF should be saved (optional, auto-generates if not provided)
                profile: Configuration profile name (default: 'default')

            Returns:
                Dictionary with download result including saved file path
            """
            try:
                client = await self.client_manager.get_client(profile)

                # Download sales confirmation with preset configuration
                saved_path = await client.download_srs_report(
                    document_id=confirmation_id,
                    legal_entity=legal_entity,
                    controller_name="SalesConfirmController",
                    data_table="CustConfirmJour",
                    data_field="ConfirmId",
                    document_type="SalesConfirmation",
                    save_path=save_path,
                )

                return {
                    "success": True,
                    "confirmation_id": confirmation_id,
                    "legal_entity": legal_entity,
                    "saved_path": saved_path,
                    "file_size_bytes": Path(saved_path).stat().st_size,
                    "message": f"Sales confirmation downloaded successfully to: {saved_path}",
                }

            except Exception as e:
                logger.error(f"Download sales confirmation failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "tool": "d365fo_download_sales_confirmation",
                    "confirmation_id": confirmation_id,
                    "legal_entity": legal_entity,
                }

        @self.mcp.tool()
        async def d365fo_download_purchase_order(
            purchase_order_id: str,
            legal_entity: str,
            save_path: str = None,
            profile: str = "default",
        ) -> dict[str, Any]:
            """Download a purchase order report as PDF from D365 Finance & Operations.

            This is a convenience tool specifically configured for purchase orders using
            the PurchPurchaseOrderController. Purchase orders are documents sent to vendors
            to order goods or services.

            To find available purchase orders to download, query the Purchase Order Confirmation Headers entity:
            - Entity name: PurchPurchaseOrderConfirmationHeaderEntity
            - Collection name: PurchaseOrderConfirmationHeaders
            - Key fields: PurchaseOrderNumber, ConfirmationNumber, ConfirmationDate, OrderVendorAccountNumber, TotalConfirmedAmount, dataAreaId
            - Use d365fo_query_entities tool to search for purchase orders

            Example query to find purchase orders:
                d365fo_query_entities(
                    entityName="PurchaseOrderConfirmationHeaders",
                    filter="ConfirmDate ge 2024-01-01",
                    select=["PurchaseOrderNumber", "ConfirmDate", "VendorAccount", "OrderStatus"]
                )

            Args:
                purchase_order_id: The purchase order ID (e.g., 'PO-000123', 'P00001234')
                legal_entity: The legal entity/company code (e.g., 'USMF', 'DEMF')
                save_path: Full path where PDF should be saved (optional, auto-generates if not provided)
                profile: Configuration profile name (default: 'default')

            Returns:
                Dictionary with download result including saved file path
            """
            try:
                client = await self.client_manager.get_client(profile)

                # Download purchase order with preset configuration
                saved_path = await client.download_srs_report(
                    document_id=purchase_order_id,
                    legal_entity=legal_entity,
                    controller_name="PurchPurchaseOrderController",
                    data_table="VendPurchOrderJour",
                    data_field="PurchId",
                    document_type="PurchaseConfirmation",
                    save_path=save_path,
                )

                return {
                    "success": True,
                    "purchase_order_id": purchase_order_id,
                    "legal_entity": legal_entity,
                    "saved_path": saved_path,
                    "file_size_bytes": Path(saved_path).stat().st_size,
                    "message": f"Purchase order downloaded successfully to: {saved_path}",
                }

            except Exception as e:
                logger.error(f"Download purchase order failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "tool": "d365fo_download_purchase_order",
                    "purchase_order_id": purchase_order_id,
                    "legal_entity": legal_entity,
                }

        logger.info("Registered 6 SRS report download tools")
