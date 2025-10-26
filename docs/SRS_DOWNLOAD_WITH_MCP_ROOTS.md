# SRS Report Download with MCP Roots Integration

This guide explains how to use the SRS report download functionality with MCP (Model Context Protocol) Roots to enable AI assistants to save reports to appropriate file system locations.

## Overview

The D365FO MCP server provides three tools for downloading SRS (SQL Server Reporting Services) reports from D365 Finance & Operations:

1. **`d365fo_download_srs_report`**: Generic tool for any SRS report type
2. **`d365fo_download_customer_invoice`**: Convenience tool for customer invoices
3. **`d365fo_download_free_text_invoice`**: Convenience tool for free text invoices

All tools support **MCP Roots** to enable AI assistants to determine appropriate save locations based on the client's file system context.

## What are MCP Roots?

MCP Roots are a protocol feature that allows clients to expose filesystem directories to the MCP server. When a client provides roots, the server can:

- Discover available storage locations
- Request permission to write to specific directories
- Respect client-side file system boundaries
- Enable AI assistants to save files to user-appropriate locations

**MCP Roots Specification**: https://modelcontextprotocol.io/specification/2025-06-18/client/roots

## Architecture

```
┌──────────────────┐         ┌──────────────────┐         ┌────────────────┐
│  AI Assistant    │         │   MCP Client     │         │  D365FO MCP    │
│  (Claude, etc)   │◄───────►│  (Claude Code,   │◄───────►│    Server      │
│                  │         │   MCP Inspector) │         │                │
└──────────────────┘         └──────────────────┘         └────────────────┘
                                      │                            │
                                      │ Provides Roots             │
                                      ▼                            ▼
                             ┌────────────────┐         ┌────────────────────┐
                             │  File System   │         │  D365 F&O API      │
                             │  Directories   │         │  SrsFinanceCopilots│
                             └────────────────┘         └────────────────────┘
```

## How It Works

### 1. Client Configuration (MCP Roots)

The MCP client exposes roots to the server. Example configuration:

```json
{
  "roots": [
    {
      "uri": "file:///home/user/Documents/D365Reports",
      "name": "D365 Reports"
    },
    {
      "uri": "file:///home/user/Projects/invoices",
      "name": "Invoice Archive"
    }
  ]
}
```

### 2. AI Assistant Query

User asks: "Download customer invoices CIV-000708 and FTI-00000021 for legal entity USMF"

### 3. Server Processing

The MCP server:
1. Receives the roots from the client
2. Determines appropriate save location
3. Downloads the report from D365 F&O
4. Saves the PDF to the specified root directory
5. Returns the saved file path to the assistant

### 4. Tool Execution

```python
# Tool: d365fo_download_customer_invoice
{
  "invoice_id": "CIV-000708",
  "legal_entity": "USMF",
  "save_path": "/home/user/Documents/D365Reports/CIV-000708.pdf"  # Derived from roots
}
```

## Tool Usage Examples

### Example 1: Download Customer Invoice with MCP Roots

**User Prompt:**
```
Download customer invoice CIV-000708 for legal entity USMF and save it to my D365 Reports folder
```

**AI Assistant Action:**
1. Lists available MCP roots
2. Selects appropriate directory (e.g., "D365 Reports")
3. Calls tool with full path

**Tool Call:**
```json
{
  "tool": "d365fo_download_customer_invoice",
  "arguments": {
    "invoice_id": "CIV-000708",
    "legal_entity": "USMF",
    "save_path": "/home/user/Documents/D365Reports/CIV-000708.pdf",
    "profile": "default"
  }
}
```

**Response:**
```json
{
  "success": true,
  "invoice_id": "CIV-000708",
  "legal_entity": "USMF",
  "saved_path": "/home/user/Documents/D365Reports/CIV-000708.pdf",
  "file_size_bytes": 245678,
  "message": "Customer invoice downloaded successfully to: /home/user/Documents/D365Reports/CIV-000708.pdf"
}
```

### Example 2: Download Multiple Invoices

**User Prompt:**
```
Download invoices CIV-000708 and FTI-00000021 for USMF to my invoice archive
```

**AI Assistant Actions:**
1. Identifies two invoices (one customer invoice, one free text invoice)
2. Selects "Invoice Archive" root
3. Makes two tool calls with appropriate controllers

**Tool Calls:**
```json
// Call 1: Customer Invoice
{
  "tool": "d365fo_download_customer_invoice",
  "arguments": {
    "invoice_id": "CIV-000708",
    "legal_entity": "USMF",
    "save_path": "/home/user/Projects/invoices/2024/CIV-000708.pdf"
  }
}

// Call 2: Free Text Invoice
{
  "tool": "d365fo_download_free_text_invoice",
  "arguments": {
    "invoice_id": "FTI-00000021",
    "legal_entity": "USMF",
    "save_path": "/home/user/Projects/invoices/2024/FTI-00000021.pdf"
  }
}
```

### Example 3: Generic SRS Report Download

**User Prompt:**
```
Download sales confirmation SC-12345 for USMF
```

**Tool Call:**
```json
{
  "tool": "d365fo_download_srs_report",
  "arguments": {
    "document_id": "SC-12345",
    "legal_entity": "USMF",
    "controller_name": "SalesConfirmController",
    "data_table": "CustConfirmJour",
    "data_field": "ConfirmId",
    "document_type": "SalesConfirmation",
    "save_path": "/home/user/Documents/D365Reports/Confirmations/SC-12345.pdf"
  }
}
```

## Supported Report Controllers

| Controller Name | Report Type | Data Table | Data Field |
|----------------|-------------|------------|------------|
| `SalesInvoiceController` | Customer Invoice | `CustInvoiceJour` | `InvoiceId` |
| `FreeTextInvoiceController` | Free Text Invoice | `CustInvoiceJour` | `InvoiceId` |
| `CustDebitCreditNoteController` | Debit/Credit Note | `CustInvoiceJour` | `InvoiceId` |
| `SalesConfirmController` | Sales Confirmation | `CustConfirmJour` | `ConfirmId` |
| `PurchPurchaseOrderController` | Purchase Order | `VendPurchOrderJour` | `PurchId` |

## Client Implementation Guide

### Step 1: Configure MCP Client with Roots

**Claude Code Configuration (`.claude/mcp_settings.json`):**
```json
{
  "mcpServers": {
    "d365fo": {
      "command": "uv",
      "args": ["run", "d365fo-fastmcp-server"],
      "env": {},
      "roots": {
        "d365_reports": "file:///home/user/Documents/D365Reports",
        "invoice_archive": "file:///home/user/Projects/invoices"
      }
    }
  }
}
```

**MCP Inspector Configuration:**
```json
{
  "server": {
    "command": "d365fo-fastmcp-server",
    "transport": "stdio"
  },
  "roots": [
    {
      "name": "D365 Reports",
      "uri": "file:///C:/Users/username/Documents/D365Reports"
    }
  ]
}
```

### Step 2: AI Assistant Usage

The AI assistant can now automatically:
1. Discover available roots
2. Ask user which location to use (if multiple roots)
3. Construct appropriate file paths
4. Download and save reports

**Example Conversation:**

```
User: Download invoice CIV-000708 for USMF

AI: I'll download that customer invoice for you. I see you have two save locations:
    1. D365 Reports
    2. Invoice Archive

    Which location would you prefer?

User: D365 Reports

AI: Downloading customer invoice CIV-000708...
    ✓ Saved to: /home/user/Documents/D365Reports/CustomerInvoice_CIV-000708_USMF_20240115_143022.pdf
    File size: 245,678 bytes
```

## Auto-Generated Filenames

When `save_path` is not specified, the system auto-generates filenames with the pattern:

```
{DocumentType}_{DocumentId}_{LegalEntity}_{Timestamp}.pdf
```

**Examples:**
- `CustomerInvoice_CIV-000708_USMF_20240115_143022.pdf`
- `FreeTextInvoice_FTI-00000021_USMF_20240115_143025.pdf`
- `PurchaseOrder_PO-12345_DEMF_20240115_143030.pdf`

## Error Handling

The tools provide comprehensive error handling:

### Invalid Document ID
```json
{
  "success": false,
  "error": "No PDF content returned from SRS report generation for document 'INVALID-ID'. The report may not exist or the document ID may be invalid.",
  "tool": "d365fo_download_customer_invoice",
  "invoice_id": "INVALID-ID",
  "legal_entity": "USMF"
}
```

### Missing Parameters
```json
{
  "success": false,
  "error": "document_id and legal_entity are required. Got document_id='', legal_entity='USMF'",
  "tool": "d365fo_download_customer_invoice"
}
```

### File System Errors
```json
{
  "success": false,
  "error": "Failed to save PDF file to '/invalid/path/invoice.pdf': [Errno 13] Permission denied",
  "tool": "d365fo_download_customer_invoice",
  "invoice_id": "CIV-000708",
  "legal_entity": "USMF"
}
```

## Best Practices

### 1. Directory Organization
Organize reports by:
- **Legal Entity**: `/D365Reports/USMF/`, `/D365Reports/DEMF/`
- **Document Type**: `/D365Reports/Invoices/`, `/D365Reports/PurchaseOrders/`
- **Date**: `/D365Reports/2024/01/`, `/D365Reports/2024/02/`

### 2. Naming Conventions
- Use descriptive document types in filenames
- Include legal entity for multi-company environments
- Add timestamps to prevent overwrites

### 3. Permission Management
- Ensure MCP client has write permissions to root directories
- Use appropriate security boundaries
- Don't expose sensitive directories as roots

### 4. Batch Operations
For downloading multiple reports:
- Use appropriate rate limiting
- Handle errors gracefully for each document
- Provide progress feedback to users

## Integration Testing

Test the SRS download functionality with:

```bash
# Run integration tests
./tests/integration/integration-test-simple.ps1 test-sandbox -VerboseOutput

# Run specific SRS tests
uv run pytest tests/integration/test_srs_download.py -v
```

## Programmatic Usage (Python)

Direct Python usage without MCP:

```python
from d365fo_client import FOClient, FOClientConfig
from pathlib import Path

async def download_invoice():
    config = FOClientConfig(
        base_url="https://your-env.dynamics.com",
        use_default_credentials=True
    )

    async with FOClient(config) as client:
        # Download with custom path
        path = await client.download_srs_report(
            document_id="CIV-000708",
            legal_entity="USMF",
            controller_name="SalesInvoiceController",
            save_path="/path/to/save/invoice.pdf"
        )

        print(f"Downloaded to: {path}")
        print(f"File size: {Path(path).stat().st_size} bytes")
```

## Security Considerations

1. **Access Control**: Ensure users have permissions to access requested documents in D365 F&O
2. **File System Security**: Root directories should have appropriate permissions
3. **Path Traversal**: The system automatically creates parent directories but validates paths
4. **Legal Entity Validation**: Always verify users have access to the specified legal entity
5. **Audit Logging**: Monitor report downloads for compliance requirements

## Troubleshooting

### Reports Not Generating
- Verify document exists in D365 F&O
- Check legal entity is correct
- Ensure controller name matches document type
- Verify user has permission to generate reports

### File Save Errors
- Check write permissions on target directory
- Verify disk space availability
- Ensure path doesn't exceed OS limits
- Check for special characters in filenames

### MCP Roots Not Working
- Verify client supports MCP Roots specification
- Check root URIs are valid file:// URIs
- Ensure roots are configured correctly in client settings
- Test with MCP Inspector for debugging

## Additional Resources

- **MCP Specification**: https://modelcontextprotocol.io/specification/2025-06-18/client/roots
- **D365FO Client Documentation**: See `README.md`
- **Example Code**: See `examples/srs_download_example.py`
- **Integration Tests**: See `tests/integration/test_srs_download.py`
