# Integration Test Coverage Report

Generated: August 21, 2025  
Test Suite: Integration Tests (Mock Server)  
Test Results: 20 passed, 5 failed, 3 warnings  
Overall Coverage: **36%**

## Coverage Summary

| Module | Statements | Missing | Coverage |
|--------|------------|---------|----------|
| **High Coverage (>80%)** |
| exceptions.py | 16 | 0 | **100%** |
| mcp/models.py | 271 | 6 | **98%** |
| session.py | 25 | 2 | **92%** |
| models.py | 322 | 37 | **89%** |
| crud.py | 68 | 12 | **82%** |
| query.py | 53 | 10 | **81%** |
| **Medium Coverage (40-80%)** |
| labels.py | 204 | 76 | **63%** |
| utils.py | 51 | 21 | **59%** |
| auth.py | 40 | 20 | **50%** |
| client.py | 350 | 201 | **43%** |
| metadata_api.py | 259 | 148 | **43%** |
| profiles.py | 78 | 47 | **40%** |
| **Low Coverage (<40%)** |
| mcp/resources/query_handler.py | 34 | 22 | **35%** |
| mcp/tools/connection_tools.py | 47 | 32 | **32%** |
| mcp/resources/entity_handler.py | 46 | 33 | **28%** |
| mcp/resources/environment_handler.py | 53 | 38 | **28%** |
| mcp/tools/label_tools.py | 54 | 39 | **28%** |
| metadata_sync.py | 184 | 135 | **27%** |
| metadata_cache.py | 949 | 730 | **23%** |
| mcp/tools/crud_tools.py | 107 | 83 | **22%** |
| config.py | 123 | 99 | **20%** |
| profile_manager.py | 128 | 102 | **20%** |
| output.py | 97 | 79 | **19%** |
| mcp/resources/metadata_handler.py | 85 | 70 | **18%** |
| mcp/tools/metadata_tools.py | 118 | 97 | **18%** |
| mcp/tools/profile_tools.py | 175 | 146 | **17%** |
| mcp/client_manager.py | 120 | 102 | **15%** |
| cli.py | 398 | 360 | **10%** |
| mcp/server.py | 211 | 189 | **10%** |
| main.py | 245 | 230 | **6%** |
| mcp/main.py | 46 | 46 | **0%** |
| metadata.py | 112 | 112 | **0%** |

## Test Results Analysis

### Passing Tests (20/25)
✅ **Connection Tests**
- Basic connection functionality
- Metadata connection validation

✅ **Version Methods**
- Application version retrieval
- Platform build version retrieval  
- Parallel version method execution

✅ **CRUD Operations** (Most)
- Customer data retrieval
- Customer creation and updates
- Customer deletion
- Query options handling

✅ **Metadata API** (Most)
- Data entities retrieval
- Public entities access
- Public enumerations access

✅ **Error Handling**
- Nonexistent entity handling
- Nonexistent label handling

✅ **Performance Tests**
- Concurrent request handling
- Large dataset processing

### Failing Tests (5/25)
❌ **CRUD Operations**
- `test_get_customer_by_key` - Entity lookup by key failing

❌ **Metadata API**
- `test_search_data_entities` - Missing entity_set_name attribute
- `test_get_public_entity_info` - Missing enhanced_properties attribute

❌ **Label Operations**
- `test_get_label_text` - Label retrieval returning None
- `test_get_labels_batch` - Batch label retrieval not working

### Key Coverage Areas

#### Well-Tested Components
1. **Core Data Models** (89%) - Data structures and validation
2. **HTTP Session Management** (92%) - Connection handling
3. **CRUD Operations** (82%) - Basic data operations
4. **Query Building** (81%) - OData query construction
5. **Exception Handling** (100%) - Error handling

#### Areas Needing Improvement
1. **CLI Interface** (10%) - Command line functionality
2. **MCP Server** (10%) - Model Context Protocol server
3. **Main Entry Points** (6-0%) - Application entry points
4. **Metadata Caching** (23%) - Caching system
5. **Profile Management** (20%) - Configuration profiles

## Environment Coverage

The integration tests primarily covered:
- **Mock Server Environment** - Local HTTP server simulation
- **Core Client Functionality** - Basic D365 F&O operations
- **Authentication Flow** - Azure AD integration
- **Metadata Operations** - Entity and schema discovery
- **Data Operations** - CRUD operations on entities

## Recommendations

### For Better Coverage
1. **Increase CLI Testing** - Add integration tests for command-line operations
2. **MCP Server Integration** - Test Model Context Protocol functionality
3. **Metadata Caching** - Test cache operations with real data
4. **Profile Management** - Test configuration and profile handling
5. **Error Scenarios** - Test more failure conditions

### For Test Stability
1. **Fix Mock Server** - Address the 5 failing tests
2. **Label Resolution** - Implement proper label mock responses
3. **Entity Schema** - Complete mock entity schema responses
4. **Key Lookups** - Fix entity lookup by key functionality

## Coverage Report Location

The detailed HTML coverage report is available at:
`htmlcov/index.html`

Open this file in a web browser to see:
- Line-by-line coverage details
- Interactive source code viewing
- Coverage statistics by module
- Missing line identification

## Test Execution Summary

```
Platform: Windows (win32)
Python: 3.13.6
Pytest: 8.4.1
Test Runner: uv run pytest
Execution Time: 3.82 seconds
Total Statements: 5,229
Missing Statements: 3,372
Coverage: 36%
```

The integration tests provide a solid foundation for testing D365 Finance & Operations client functionality, with particularly strong coverage of core data operations and HTTP handling. The mock server approach enables fast, reliable testing without external dependencies.