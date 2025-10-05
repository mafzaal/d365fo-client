# DMF Operations Implementation - Quick Summary

## Overview

Implementation specification for exposing 25 Data Management Framework (DMF) actions from the `DataManagementDefinitionGroup` entity in d365fo-client.

## Architecture

```
FOClient
  └─> DmfOperations (new class)
       └─> 25 async methods for DMF actions

FastD365FOMCPServer
  └─> DmfToolsMixin (new mixin)
       └─> MCP tools for common DMF operations
```

## Key Files to Create

1. **`src/d365fo_client/dmf_operations.py`** (~800 lines)
   - DmfOperations class with 25 action methods
   - All actions bound to `DataManagementDefinitionGroups` entity set
   - Comprehensive docstrings and error handling

2. **`src/d365fo_client/mcp/mixins/dmf_tools_mixin.py`** (~400 lines)
   - DmfToolsMixin class
   - MCP tools for most common operations
   - Tool registration method

## Files to Modify

1. **`src/d365fo_client/client.py`**
   - Add `self.dmf_ops = DmfOperations(...)` in `__init__`
   - Add 25 delegate methods for DMF operations

2. **`src/d365fo_client/models.py`**
   - Add DMF data models (DMFExecutionStatus, DMFExportOptions, etc.)

3. **`src/d365fo_client/exceptions.py`**
   - Add DMFError exception classes

4. **`src/d365fo_client/mcp/mixins/__init__.py`**
   - Export DmfToolsMixin

5. **`src/d365fo_client/mcp/fastmcp_server.py`**
   - Add DmfToolsMixin to inheritance
   - Call `self.register_dmf_tools()` in `_register_tools()`

## Action Categories (25 Total)

### Export Operations (7)
- ExportToPackage, ExportToPackageAsync
- ExportToPackagePreview, ExportToPackagePreviewAsync  
- ExportToPackageDelta, ExportFromPackage
- GetExportedPackageUrl

### Import Operations (2)
- ImportFromPackage, ImportFromDMTPackage

### Initialization (2)
- InitializeDataManagement, InitializeDataManagementAsync

### Status & Monitoring (3)
- GetExecutionSummaryStatus
- GetEntityExecutionSummaryStatusList
- GetMessageStatus

### Error Management (4)
- GetExecutionErrors
- GetImportTargetErrorKeysFileUrl
- GetImportStagingErrorFileUrl
- GenerateImportTargetErrorKeysFile

### Utilities (6)
- GetAzureWriteUrl, GetEntitySequence
- ResetVersionToken, GetExecutionIdByMessageId

## Implementation Pattern

### FOClient Method Example
```python
async def export_to_package(
    self,
    definition_group_id: str,
    package_name: str,
    execution_id: str = "",
    re_execute: bool = False,
    legal_entity_id: str = "",
) -> str:
    """Export data to package (synchronous)."""
    await self._ensure_metadata_initialized()
    return await self.dmf_ops.export_to_package(
        definition_group_id, package_name, execution_id, 
        re_execute, legal_entity_id
    )
```

### MCP Tool Example
```python
@self.mcp.tool()
async def d365fo_dmf_export_to_package(
    definition_group_id: str,
    package_name: str,
    execution_id: str = "",
    re_execute: bool = False,
    legal_entity_id: str = "",
    profile: str = "default",
) -> dict:
    """Export data to package from D365FO."""
    try:
        client = await self._get_client(profile)
        result = await client.export_to_package(...)
        return {"success": True, "execution_id": result, ...}
    except Exception as e:
        return self._create_error_response(e, ...)
```

## URL Construction

All actions use this pattern (BoundToEntitySet):
```
{base_url}/data/DataManagementDefinitionGroups/Microsoft.Dynamics.DataEntities.{ActionName}
```

Example:
```
https://example.dynamics.com/data/DataManagementDefinitionGroups/Microsoft.Dynamics.DataEntities.ExportToPackage
```

## Testing Requirements

1. **Unit Tests** - Mock HTTP calls, test logic
2. **Integration Tests** - Test against sandbox environment
3. **MCP Tests** - Validate tool registration and execution

## Usage Example

```python
from d365fo_client import FOClient, FOClientConfig

config = FOClientConfig(
    base_url="https://example.dynamics.com",
    credential_source=None,
)

async with FOClient(config) as client:
    # Export data
    execution_id = await client.export_to_package_async(
        definition_group_id="CustomerData",
        package_name="Customers_2025-10-05",
        legal_entity_id="USMF"
    )
    
    print(f"Export started: {execution_id}")
    
    # Check status
    status = await client.get_execution_summary_status(execution_id)
    print(f"Status: {status}")
    
    # Download package
    url = await client.get_exported_package_url(execution_id)
    print(f"Download: {url}")
```

## Key Design Decisions

1. **Separate Class**: DmfOperations follows existing pattern (CrudOperations, MetadataAPIOperations)
2. **All BoundToEntitySet**: Consistent URL construction for all 25 actions
3. **Async-First**: All operations are async
4. **Type Safe**: Full type hints throughout
5. **Comprehensive Errors**: DMFError with execution_id and error_details
6. **MCP Subset**: Expose most common operations as MCP tools

## Implementation Phases

### Phase 1: Core (2-3 days)
- Create DmfOperations class
- Add data models and exceptions
- Integrate into FOClient
- Unit tests

### Phase 2: MCP Integration (1-2 days)
- Create DmfToolsMixin
- Register tools
- MCP tests

### Phase 3: Documentation (1 day)
- Docstrings
- Examples
- README updates
- Integration tests

## Success Criteria

- ✅ All 25 actions implemented and working
- ✅ Type safe with proper hints
- ✅ >90% test coverage
- ✅ MCP tools registered and functional
- ✅ Complete documentation
- ✅ Integration tests pass

## References

- Full specification: `DMF_OPERATIONS_IMPLEMENTATION_SPEC.md`
- Entity schema analysis: Terminal output with all 25 actions
- Existing patterns: `crud.py`, `metadata_api.py`, `crud_tools_mixin.py`
