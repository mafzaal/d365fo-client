"""Integration tests for SRS report download functionality.

These tests verify the SRS report download feature against real D365 F&O environments.
Tests include downloading various report types with different configurations and validating
the generated PDF files.

Test levels:
- mock: Tests against mock server (not applicable for SRS reports)
- sandbox: Tests against sandbox/test environment with known test data
- live: Tests against live/production environment (use with caution)
"""

import tempfile
from pathlib import Path

import pytest

from d365fo_client import FOClient
from d365fo_client.exceptions import FOClientError

# Test data - these should exist in your sandbox environment
TEST_CUSTOMER_INVOICE_ID = (
    "CIV-000708"  # Replace with actual invoice ID in your sandbox
)
TEST_FREE_TEXT_INVOICE_ID = "FTI-00000021"  # Replace with actual FTI ID in your sandbox
TEST_LEGAL_ENTITY = "USMF"  # Replace with your test legal entity


class TestSRSDownload:
    """Test SRS report download functionality."""

    @pytest.mark.integration
    @pytest.mark.sandbox
    async def test_download_customer_invoice_auto_path(self, sandbox_client: FOClient):
        """Test downloading customer invoice with auto-generated path."""
        # Download invoice
        saved_path = await sandbox_client.download_srs_report(
            document_id=TEST_CUSTOMER_INVOICE_ID,
            legal_entity=TEST_LEGAL_ENTITY,
            controller_name="SalesInvoiceController",
            data_table="CustInvoiceJour",
            data_field="InvoiceId",
            document_type="CustomerInvoice",
        )

        # Verify file was created
        assert saved_path is not None
        assert Path(saved_path).exists()
        assert Path(saved_path).suffix == ".pdf"
        assert Path(saved_path).stat().st_size > 0

        # Verify filename contains expected components
        filename = Path(saved_path).name
        assert "CustomerInvoice" in filename
        assert TEST_CUSTOMER_INVOICE_ID in filename
        assert TEST_LEGAL_ENTITY in filename

        # Verify PDF header (magic bytes)
        with open(saved_path, "rb") as f:
            header = f.read(4)
            assert header == b"%PDF", "File is not a valid PDF"

        # Cleanup
        Path(saved_path).unlink(missing_ok=True)
        # Also cleanup parent directory if it's the default ./Reports
        if Path(saved_path).parent.name == "Reports":
            try:
                Path(saved_path).parent.rmdir()
            except OSError:
                pass  # Directory not empty or doesn't exist

    @pytest.mark.integration
    @pytest.mark.sandbox
    async def test_download_customer_invoice_custom_path(
        self, sandbox_client: FOClient
    ):
        """Test downloading customer invoice with custom save path."""
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_path = (
                Path(temp_dir) / "invoices" / f"{TEST_CUSTOMER_INVOICE_ID}.pdf"
            )

            # Download invoice
            saved_path = await sandbox_client.download_srs_report(
                document_id=TEST_CUSTOMER_INVOICE_ID,
                legal_entity=TEST_LEGAL_ENTITY,
                controller_name="SalesInvoiceController",
                data_table="CustInvoiceJour",
                data_field="InvoiceId",
                document_type="CustomerInvoice",
                save_path=str(custom_path),
            )

            # Verify file was created at custom path
            assert saved_path == str(custom_path.resolve())
            assert Path(saved_path).exists()
            assert Path(saved_path).stat().st_size > 0

            # Verify PDF header
            with open(saved_path, "rb") as f:
                header = f.read(4)
                assert header == b"%PDF", "File is not a valid PDF"

    @pytest.mark.integration
    @pytest.mark.sandbox
    async def test_download_free_text_invoice(self, sandbox_client: FOClient):
        """Test downloading free text invoice."""
        # Download free text invoice
        saved_path = await sandbox_client.download_srs_report(
            document_id=TEST_FREE_TEXT_INVOICE_ID,
            legal_entity=TEST_LEGAL_ENTITY,
            controller_name="FreeTextInvoiceController",
            data_table="CustInvoiceJour",
            data_field="InvoiceId",
            document_type="FreeTextInvoice",
        )

        # Verify file was created
        assert saved_path is not None
        assert Path(saved_path).exists()
        assert Path(saved_path).suffix == ".pdf"
        assert Path(saved_path).stat().st_size > 0

        # Verify filename contains expected components
        filename = Path(saved_path).name
        assert "FreeTextInvoice" in filename
        assert TEST_FREE_TEXT_INVOICE_ID in filename

        # Verify PDF header
        with open(saved_path, "rb") as f:
            header = f.read(4)
            assert header == b"%PDF", "File is not a valid PDF"

        # Cleanup
        Path(saved_path).unlink(missing_ok=True)
        if Path(saved_path).parent.name == "Reports":
            try:
                Path(saved_path).parent.rmdir()
            except OSError:
                pass

    @pytest.mark.integration
    @pytest.mark.sandbox
    async def test_download_invalid_document_id(self, sandbox_client: FOClient):
        """Test downloading with invalid document ID."""
        with pytest.raises(FOClientError) as exc_info:
            await sandbox_client.download_srs_report(
                document_id="INVALID-DOCUMENT-ID-999999",
                legal_entity=TEST_LEGAL_ENTITY,
                controller_name="SalesInvoiceController",
            )

        # Verify error message indicates no PDF content
        assert "No PDF content returned" in str(
            exc_info.value
        ) or "Failed to download" in str(exc_info.value)

    @pytest.mark.integration
    @pytest.mark.sandbox
    async def test_download_missing_parameters(self, sandbox_client: FOClient):
        """Test downloading with missing required parameters."""
        # Missing document_id
        with pytest.raises(ValueError) as exc_info:
            await sandbox_client.download_srs_report(
                document_id="",
                legal_entity=TEST_LEGAL_ENTITY,
            )
        assert "document_id and legal_entity are required" in str(exc_info.value)

        # Missing legal_entity
        with pytest.raises(ValueError) as exc_info:
            await sandbox_client.download_srs_report(
                document_id=TEST_CUSTOMER_INVOICE_ID,
                legal_entity="",
            )
        assert "document_id and legal_entity are required" in str(exc_info.value)

    @pytest.mark.integration
    @pytest.mark.sandbox
    async def test_download_multiple_reports_batch(self, sandbox_client: FOClient):
        """Test downloading multiple reports in a batch."""
        document_ids = [TEST_CUSTOMER_INVOICE_ID, TEST_FREE_TEXT_INVOICE_ID]
        saved_paths = []

        try:
            # Download multiple reports
            for doc_id in document_ids:
                # Determine controller based on ID prefix
                if doc_id.startswith("FTI"):
                    controller = "FreeTextInvoiceController"
                    doc_type = "FreeTextInvoice"
                else:
                    controller = "SalesInvoiceController"
                    doc_type = "CustomerInvoice"

                saved_path = await sandbox_client.download_srs_report(
                    document_id=doc_id,
                    legal_entity=TEST_LEGAL_ENTITY,
                    controller_name=controller,
                    document_type=doc_type,
                )
                saved_paths.append(saved_path)

            # Verify all files were created
            assert len(saved_paths) == len(document_ids)
            for saved_path in saved_paths:
                assert Path(saved_path).exists()
                assert Path(saved_path).stat().st_size > 0

                # Verify PDF header
                with open(saved_path, "rb") as f:
                    header = f.read(4)
                    assert header == b"%PDF", f"File {saved_path} is not a valid PDF"

        finally:
            # Cleanup all generated files
            for saved_path in saved_paths:
                if saved_path and Path(saved_path).exists():
                    Path(saved_path).unlink(missing_ok=True)

            # Cleanup Reports directory if it exists and is empty
            reports_dir = Path("./Reports")
            if reports_dir.exists():
                try:
                    reports_dir.rmdir()
                except OSError:
                    pass  # Directory not empty

    @pytest.mark.integration
    @pytest.mark.sandbox
    async def test_download_with_path_object(self, sandbox_client: FOClient):
        """Test downloading with Path object instead of string."""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_path = Path(temp_dir) / "test_invoice.pdf"

            # Download using Path object
            saved_path = await sandbox_client.download_srs_report(
                document_id=TEST_CUSTOMER_INVOICE_ID,
                legal_entity=TEST_LEGAL_ENTITY,
                save_path=custom_path,  # Pass Path object directly
            )

            # Verify file was created
            assert Path(saved_path).exists()
            assert Path(saved_path).stat().st_size > 0

    @pytest.mark.integration
    @pytest.mark.sandbox
    async def test_download_creates_parent_directories(self, sandbox_client: FOClient):
        """Test that parent directories are created automatically."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Use nested path that doesn't exist
            nested_path = (
                Path(temp_dir) / "level1" / "level2" / "level3" / "invoice.pdf"
            )

            # Download - should create all parent directories
            saved_path = await sandbox_client.download_srs_report(
                document_id=TEST_CUSTOMER_INVOICE_ID,
                legal_entity=TEST_LEGAL_ENTITY,
                save_path=str(nested_path),
            )

            # Verify file was created and parent directories exist
            assert Path(saved_path).exists()
            assert Path(saved_path).parent.exists()
            assert Path(saved_path).parent.parent.exists()

    @pytest.mark.integration
    @pytest.mark.sandbox
    async def test_download_file_size_reasonable(self, sandbox_client: FOClient):
        """Test that downloaded PDF has reasonable file size."""
        saved_path = await sandbox_client.download_srs_report(
            document_id=TEST_CUSTOMER_INVOICE_ID,
            legal_entity=TEST_LEGAL_ENTITY,
        )

        try:
            file_size = Path(saved_path).stat().st_size

            # PDF should be at least 1KB and less than 10MB (reasonable bounds)
            assert file_size > 1024, "PDF file is too small, might be corrupted"
            assert file_size < 10 * 1024 * 1024, "PDF file is unexpectedly large"

        finally:
            Path(saved_path).unlink(missing_ok=True)
            if Path(saved_path).parent.name == "Reports":
                try:
                    Path(saved_path).parent.rmdir()
                except OSError:
                    pass


class TestSRSDownloadEdgeCases:
    """Test edge cases and error handling for SRS download."""

    @pytest.mark.integration
    @pytest.mark.sandbox
    async def test_download_with_special_characters_in_path(
        self, sandbox_client: FOClient
    ):
        """Test downloading to path with special characters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Path with spaces and special characters
            custom_path = (
                Path(temp_dir)
                / "My Invoices 2024"
                / f"Invoice {TEST_CUSTOMER_INVOICE_ID}.pdf"
            )

            saved_path = await sandbox_client.download_srs_report(
                document_id=TEST_CUSTOMER_INVOICE_ID,
                legal_entity=TEST_LEGAL_ENTITY,
                save_path=str(custom_path),
            )

            assert Path(saved_path).exists()
            assert Path(saved_path).stat().st_size > 0

    @pytest.mark.integration
    @pytest.mark.sandbox
    async def test_download_overwrites_existing_file(self, sandbox_client: FOClient):
        """Test that downloading overwrites existing file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_path = Path(temp_dir) / "invoice.pdf"

            # Create dummy file
            custom_path.write_text("dummy content")
            original_size = custom_path.stat().st_size

            # Download - should overwrite
            saved_path = await sandbox_client.download_srs_report(
                document_id=TEST_CUSTOMER_INVOICE_ID,
                legal_entity=TEST_LEGAL_ENTITY,
                save_path=str(custom_path),
            )

            # Verify file was overwritten with real PDF
            assert Path(saved_path).exists()
            new_size = Path(saved_path).stat().st_size
            assert new_size != original_size
            assert new_size > 1024  # Real PDF should be larger

            # Verify it's a valid PDF
            with open(saved_path, "rb") as f:
                header = f.read(4)
                assert header == b"%PDF"


# Configuration for pytest-asyncio
pytestmark = pytest.mark.asyncio
