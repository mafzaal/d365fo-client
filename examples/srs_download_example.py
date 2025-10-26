"""Example demonstrating SRS report download functionality.

This example shows how to download various types of SRS reports from D365 F&O
including customer invoices, free text invoices, and custom reports.

Prerequisites:
- D365FO environment credentials configured
- Valid document IDs that exist in the environment
- Write permissions to save PDFs
"""

import asyncio
import os
from pathlib import Path

from d365fo_client import FOClient, FOClientConfig


async def example_download_customer_invoice():
    """Example: Download a customer invoice with auto-generated path."""
    print("\n=== Example 1: Download Customer Invoice (Auto Path) ===")

    config = FOClientConfig(
        base_url=os.getenv(
            "D365FO_BASE_URL", "https://usnconeboxax1aos.cloud.onebox.dynamics.com/"
        ),
        verify_ssl=False,  # Set to True in production
        # credential_source=None (default) uses Azure Default Credentials
    )

    async with FOClient(config) as client:
        # Download customer invoice - file will be saved in ./Reports/
        saved_path = await client.download_srs_report(
            document_id="CIV-000708",
            legal_entity="USMF",
            controller_name="SalesInvoiceController",
            data_table="CustInvoiceJour",
            data_field="InvoiceId",
            document_type="CustomerInvoice",
        )

        print(f"✓ Customer invoice downloaded to: {saved_path}")
        print(f"  File size: {Path(saved_path).stat().st_size:,} bytes")


async def example_download_with_custom_path():
    """Example: Download invoice to a specific custom path."""
    print("\n=== Example 2: Download to Custom Path ===")

    config = FOClientConfig(
        base_url=os.getenv(
            "D365FO_BASE_URL", "https://usnconeboxax1aos.cloud.onebox.dynamics.com/"
        ),
        verify_ssl=False,  # Set to True in production
    )

    async with FOClient(config) as client:
        # Create custom directory structure
        custom_path = (
            Path.home() / "D365Reports" / "Invoices" / "2024" / "CIV-000708.pdf"
        )

        # Download to custom location
        saved_path = await client.download_srs_report(
            document_id="CIV-000708",
            legal_entity="USMF",
            controller_name="SalesInvoiceController",
            save_path=str(custom_path),
        )

        print(f"✓ Invoice downloaded to custom path: {saved_path}")
        print(f"  Directory created: {custom_path.parent}")


async def example_download_free_text_invoice():
    """Example: Download a free text invoice."""
    print("\n=== Example 3: Download Free Text Invoice ===")

    config = FOClientConfig(
        base_url=os.getenv(
            "D365FO_BASE_URL", "https://usnconeboxax1aos.cloud.onebox.dynamics.com/"
        ),
        verify_ssl=False,  # Set to True in production
    )

    async with FOClient(config) as client:
        saved_path = await client.download_srs_report(
            document_id="FTI-00000021",
            legal_entity="USMF",
            controller_name="FreeTextInvoiceController",
            data_table="CustInvoiceJour",
            data_field="InvoiceId",
            document_type="FreeTextInvoice",
        )

        print(f"✓ Free text invoice downloaded to: {saved_path}")


async def example_download_multiple_invoices():
    """Example: Download multiple invoices in batch."""
    print("\n=== Example 4: Batch Download Multiple Invoices ===")

    config = FOClientConfig(
        base_url=os.getenv(
            "D365FO_BASE_URL", "https://usnconeboxax1aos.cloud.onebox.dynamics.com/"
        ),
        verify_ssl=False,  # Set to True in production
    )

    # List of invoices to download
    invoices = [
        {
            "id": "CIV-000708",
            "type": "CustomerInvoice",
            "controller": "SalesInvoiceController",
        },
        {
            "id": "FTI-00000021",
            "type": "FreeTextInvoice",
            "controller": "FreeTextInvoiceController",
        },
    ]

    async with FOClient(config) as client:
        saved_paths = []

        for invoice in invoices:
            print(f"  Downloading {invoice['id']}...")
            saved_path = await client.download_srs_report(
                document_id=invoice["id"],
                legal_entity="USMF",
                controller_name=invoice["controller"],
                document_type=invoice["type"],
            )
            saved_paths.append(saved_path)
            print(f"    ✓ Saved to: {saved_path}")

        print(f"\n✓ Downloaded {len(saved_paths)} invoices successfully")


async def example_download_purchase_order():
    """Example: Download a purchase order report."""
    print("\n=== Example 5: Download Purchase Order ===")

    config = FOClientConfig(
        base_url=os.getenv(
            "D365FO_BASE_URL", "https://usnconeboxax1aos.cloud.onebox.dynamics.com/"
        ),
        verify_ssl=False,  # Set to True in production
    )

    async with FOClient(config) as client:
        saved_path = await client.download_srs_report(
            document_id="PO-000123",
            legal_entity="USMF",
            controller_name="PurchPurchaseOrderController",
            data_table="VendPurchOrderJour",
            data_field="PurchId",
            document_type="PurchaseOrder",
        )

        print(f"✓ Purchase order downloaded to: {saved_path}")


async def example_error_handling():
    """Example: Proper error handling for SRS downloads."""
    print("\n=== Example 6: Error Handling ===")

    config = FOClientConfig(
        base_url=os.getenv(
            "D365FO_BASE_URL", "https://usnconeboxax1aos.cloud.onebox.dynamics.com/"
        ),
        verify_ssl=False,  # Set to True in production
    )

    async with FOClient(config) as client:
        try:
            # Try to download non-existent invoice
            await client.download_srs_report(
                document_id="INVALID-ID-999999",
                legal_entity="USMF",
            )
        except ValueError as e:
            print(f"✓ Caught validation error: {e}")
        except Exception as e:
            print(f"✓ Caught error: {type(e).__name__}: {e}")


async def main():
    """Run all examples."""
    print("=" * 70)
    print("D365 F&O SRS Report Download Examples")
    print("=" * 70)

    try:
        # Run examples
        await example_download_customer_invoice()
        await example_download_with_custom_path()
        await example_download_free_text_invoice()
        await example_download_multiple_invoices()
        # await example_download_purchase_order()  # Uncomment if you have PO data
        await example_error_handling()

        print("\n" + "=" * 70)
        print("✓ All examples completed successfully!")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        print("  Make sure:")
        print("  1. D365FO_BASE_URL environment variable is set")
        print("  2. You have valid credentials configured")
        print("  3. The document IDs exist in your environment")


if __name__ == "__main__":
    # Run examples
    asyncio.run(main())
