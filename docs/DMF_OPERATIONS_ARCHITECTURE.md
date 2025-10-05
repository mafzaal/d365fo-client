# DMF Operations Architecture Diagram

## Component Hierarchy

```
┌─────────────────────────────────────────────────────────────────────┐
│                           FOClient                                   │
│                    (Main Client Interface)                           │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 │ delegates to
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        DmfOperations                                 │
│                   (DMF Operations Handler)                           │
│                                                                       │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │  Export Operations (7 actions)                             │     │
│  │  • export_to_package()                                     │     │
│  │  • export_to_package_async()                              │     │
│  │  • export_to_package_preview()                            │     │
│  │  • export_to_package_preview_async()                      │     │
│  │  • export_to_package_delta()                              │     │
│  │  • export_from_package()                                  │     │
│  │  • get_exported_package_url()                             │     │
│  └───────────────────────────────────────────────────────────┘     │
│                                                                       │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │  Import Operations (2 actions)                             │     │
│  │  • import_from_package()                                   │     │
│  │  • import_from_dmt_package()                              │     │
│  └───────────────────────────────────────────────────────────┘     │
│                                                                       │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │  Initialization (2 actions)                                │     │
│  │  • initialize_data_management()                            │     │
│  │  • initialize_data_management_async()                      │     │
│  └───────────────────────────────────────────────────────────┘     │
│                                                                       │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │  Status & Monitoring (3 actions)                           │     │
│  │  • get_execution_summary_status()                          │     │
│  │  • get_entity_execution_summary_status_list()             │     │
│  │  • get_message_status()                                    │     │
│  └───────────────────────────────────────────────────────────┘     │
│                                                                       │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │  Error Management (4 actions)                              │     │
│  │  • get_execution_errors()                                  │     │
│  │  • get_import_target_error_keys_file_url()                │     │
│  │  • get_import_staging_error_file_url()                    │     │
│  │  • generate_import_target_error_keys_file()               │     │
│  └───────────────────────────────────────────────────────────┘     │
│                                                                       │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │  Utilities (6 actions)                                     │     │
│  │  • get_azure_write_url()                                   │     │
│  │  • get_entity_sequence()                                   │     │
│  │  • reset_version_token()                                   │     │
│  │  • get_execution_id_by_message_id()                        │     │
│  └───────────────────────────────────────────────────────────┘     │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 │ uses
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      SessionManager                                  │
│                    (HTTP Session Management)                         │
└─────────────────────────────────────────────────────────────────────┘
```

## MCP Integration Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FastD365FOMCPServer                               │
│                  (FastMCP Server Instance)                           │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 │ inherits from
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        DmfToolsMixin                                 │
│                   (MCP Tools for DMF Operations)                     │
│                                                                       │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │  MCP Tools (Exposed to AI Assistants)                     │     │
│  │                                                             │     │
│  │  @mcp.tool()                                               │     │
│  │  • d365fo_dmf_export_to_package()                         │     │
│  │  • d365fo_dmf_export_to_package_async()                   │     │
│  │  • d365fo_dmf_get_exported_package_url()                  │     │
│  │  • d365fo_dmf_import_from_package()                       │     │
│  │  • d365fo_dmf_get_execution_status()                      │     │
│  │  • d365fo_dmf_get_execution_errors()                      │     │
│  │  • d365fo_dmf_get_azure_write_url()                       │     │
│  │  ... (subset of 25 operations)                            │     │
│  └───────────────────────────────────────────────────────────┘     │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 │ delegates to
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      D365FOClientManager                             │
│                    (Connection Pool Manager)                         │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 │ creates
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           FOClient                                   │
│                     (with DmfOperations)                             │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow: Export Operation

```
┌─────────────┐
│ User/AI     │
│ Assistant   │
└─────────────┘
       │
       │ 1. Call MCP Tool
       │ d365fo_dmf_export_to_package(
       │   definition_group_id="CustomerData",
       │   package_name="Export_2025-10-05",
       │   legal_entity_id="USMF"
       │ )
       ▼
┌─────────────────────────────────────────┐
│    DmfToolsMixin                         │
│    (MCP Tool Handler)                    │
└─────────────────────────────────────────┘
       │
       │ 2. Get Client from Pool
       ▼
┌─────────────────────────────────────────┐
│    D365FOClientManager                   │
└─────────────────────────────────────────┘
       │
       │ 3. Return FOClient
       ▼
┌─────────────────────────────────────────┐
│    FOClient                              │
│    .export_to_package(...)              │
└─────────────────────────────────────────┘
       │
       │ 4. Delegate to DmfOperations
       ▼
┌─────────────────────────────────────────┐
│    DmfOperations                         │
│    .export_to_package(...)              │
└─────────────────────────────────────────┘
       │
       │ 5. Build Action URL
       │ {base}/data/DataManagementDefinitionGroups/
       │ Microsoft.Dynamics.DataEntities.ExportToPackage
       │
       │ 6. HTTP POST with parameters
       ▼
┌─────────────────────────────────────────┐
│    SessionManager                        │
│    (HTTP Session with Auth)              │
└─────────────────────────────────────────┘
       │
       │ 7. Send Request
       ▼
┌─────────────────────────────────────────┐
│    D365 F&O Server                       │
│    /data/DataManagementDefinitionGroups  │
│    /Microsoft.Dynamics.DataEntities      │
│    .ExportToPackage                      │
└─────────────────────────────────────────┘
       │
       │ 8. Return Execution ID
       │ "EXEC-12345-67890"
       │
       ▼
       │ (Response flows back through layers)
       │
┌─────────────┐
│ User/AI     │ ◄── 9. Receive Result
│ Assistant   │     {
└─────────────┘       "success": true,
                      "execution_id": "EXEC-12345-67890",
                      "definition_group": "CustomerData",
                      ...
                    }
```

## URL Construction Pattern

All 25 DMF actions follow this URL pattern (BoundToEntitySet):

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Action URL Structure                         │
└─────────────────────────────────────────────────────────────────────┘

{base_url}/data/{entity_set}/{action_namespace}.{action_name}

Examples:

https://example.dynamics.com/data/DataManagementDefinitionGroups/
    Microsoft.Dynamics.DataEntities.ExportToPackage

https://example.dynamics.com/data/DataManagementDefinitionGroups/
    Microsoft.Dynamics.DataEntities.GetExecutionSummaryStatus

https://example.dynamics.com/data/DataManagementDefinitionGroups/
    Microsoft.Dynamics.DataEntities.ImportFromPackage
```

## Error Handling Flow

```
┌─────────────────────────────────────────┐
│    DmfOperations Method                  │
│    (e.g., export_to_package)            │
└─────────────────────────────────────────┘
       │
       │ try
       ▼
┌─────────────────────────────────────────┐
│    HTTP POST to Action URL               │
└─────────────────────────────────────────┘
       │
       ├─ Success (200, 201, 204)
       │  └─► Return Result
       │
       └─ Error (4xx, 5xx)
          └─► raise DMFError(
                message="Action failed: {status} - {error}",
                execution_id=execution_id,
                error_details={...}
              )
                   │
                   ▼
            ┌─────────────────────────────┐
            │    MCP Tool Handler         │
            │    (in DmfToolsMixin)       │
            └─────────────────────────────┘
                   │
                   │ catch Exception
                   ▼
            ┌─────────────────────────────┐
            │ Return Error Response        │
            │ {                            │
            │   "error": "...",            │
            │   "tool": "...",             │
            │   "arguments": {...},        │
            │   "error_type": "..."        │
            │ }                            │
            └─────────────────────────────┘
```

## File Organization

```
d365fo-client/
│
├── src/d365fo_client/
│   ├── client.py                    ◄─── Add DMF delegate methods
│   ├── dmf_operations.py            ◄─── NEW: Core DMF operations
│   ├── models.py                    ◄─── Add DMF data models
│   ├── exceptions.py                ◄─── Add DMF exceptions
│   │
│   └── mcp/
│       ├── fastmcp_server.py        ◄─── Add DmfToolsMixin to inheritance
│       │
│       └── mixins/
│           ├── __init__.py          ◄─── Export DmfToolsMixin
│           ├── dmf_tools_mixin.py   ◄─── NEW: MCP tools for DMF
│           └── ...other mixins...
│
├── docs/
│   ├── DMF_OPERATIONS_IMPLEMENTATION_SPEC.md  ◄─── Full specification
│   ├── DMF_OPERATIONS_SUMMARY.md              ◄─── Quick summary
│   └── DMF_OPERATIONS_ARCHITECTURE.md         ◄─── This document
│
├── examples/
│   ├── dmf_operations_example.py    ◄─── NEW: Usage examples
│   └── dmf_mcp_demo.py              ◄─── NEW: MCP demo
│
└── tests/
    ├── unit/
    │   └── test_dmf_operations.py   ◄─── NEW: Unit tests
    └── integration/
        └── test_dmf_integration.py  ◄─── NEW: Integration tests
```

## Class Relationships

```
┌───────────────────────────────────┐
│        BaseToolsMixin             │
│   (Common mixin functionality)    │
└───────────────────────────────────┘
                △
                │ inherits
                │
┌───────────────────────────────────┐
│        DmfToolsMixin              │
│   (DMF-specific MCP tools)        │
│                                   │
│   Properties:                     │
│   • client_manager                │
│   • mcp                           │
│   • profile_manager               │
│                                   │
│   Methods:                        │
│   • register_dmf_tools()          │
│   • _get_client(profile)          │
│   • _create_error_response(...)   │
└───────────────────────────────────┘
                △
                │ mixed into
                │
┌───────────────────────────────────┐
│    FastD365FOMCPServer            │
│   (Main MCP server)               │
│                                   │
│   Multiple Inheritance:           │
│   • DatabaseToolsMixin            │
│   • MetadataToolsMixin            │
│   • CrudToolsMixin                │
│   • DmfToolsMixin        ◄────────┼─── NEW
│   • ProfileToolsMixin             │
│   • SyncToolsMixin                │
│   • LabelToolsMixin               │
│   • ConnectionToolsMixin          │
│   • PerformanceToolsMixin         │
└───────────────────────────────────┘
```

## Sequence Diagram: Complete Export Flow

```
User      MCP Tool    ClientMgr    FOClient    DmfOps    Session    D365FO
 │            │           │           │          │          │         │
 │ Export     │           │           │          │          │         │
 │───────────>│           │           │          │          │         │
 │            │ Get       │           │          │          │         │
 │            │ Client    │           │          │          │         │
 │            │──────────>│           │          │          │         │
 │            │           │ Return    │          │          │         │
 │            │           │ FOClient  │          │          │         │
 │            │<──────────│           │          │          │         │
 │            │           │ Export    │          │          │         │
 │            │           │ Request   │          │          │         │
 │            │───────────────────────>│          │          │         │
 │            │           │           │ Delegate │          │         │
 │            │           │           │─────────>│          │         │
 │            │           │           │          │ Build    │         │
 │            │           │           │          │ URL      │         │
 │            │           │           │          │          │         │
 │            │           │           │          │ Get      │         │
 │            │           │           │          │ Session  │         │
 │            │           │           │          │─────────>│         │
 │            │           │           │          │          │ POST    │
 │            │           │           │          │          │ Action  │
 │            │           │           │          │          │────────>│
 │            │           │           │          │          │         │ Execute
 │            │           │           │          │          │         │ Export
 │            │           │           │          │          │         │
 │            │           │           │          │          │ Exec ID │
 │            │           │           │          │          │<────────│
 │            │           │           │          │<─────────│         │
 │            │           │           │<─────────│          │         │
 │            │<───────────────────────│          │          │         │
 │ Result     │           │           │          │          │         │
 │<───────────│           │           │          │          │         │
 │            │           │           │          │          │         │
```

## Implementation Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: MCP Interface (FastMCP Tools)                      │
│  • User-facing tool definitions with documentation           │
│  • Parameter validation and error handling                   │
│  • Response formatting for MCP protocol                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Client Interface (FOClient)                        │
│  • Public API for DMF operations                             │
│  • Metadata initialization                                   │
│  • Delegation to operations classes                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Operations Handler (DmfOperations)                 │
│  • Business logic for DMF operations                         │
│  • URL construction and parameter formatting                 │
│  • Response parsing and error handling                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: HTTP Layer (SessionManager)                        │
│  • HTTP client management                                    │
│  • Authentication and token refresh                          │
│  • Connection pooling and retry logic                        │
└─────────────────────────────────────────────────────────────┘
```

---

**This architecture ensures:**
- Separation of concerns across layers
- Consistent patterns with existing code
- Easy testing and maintenance
- Extensibility for future operations
- Type safety throughout the stack
