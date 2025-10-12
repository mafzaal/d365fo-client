# Entity Validation and OData Serialization Tests

This directory contains comprehensive tests for entity validation and OData serialization functionality in the d365fo-client package.

## Overview

The tests focus on:
1. **Entity Existence Validation** - Verifying entities exist across different naming formats
2. **OData Serialization** - Testing serialization for all D365 F&O data types
3. **Composite Key Discovery** - Finding and testing entities with multiple key fields
4. **Data Type Validation** - Ensuring proper handling of mixed data types in composite keys

## Test Files

### Unit Tests (No Environment Required)
- **`test_entity_validation_unit.py`** - Complete unit test suite that runs without a live D365 F&O environment
  - Tests entity name resolution logic
  - Tests OData serialization for all data types
  - Tests composite key handling with mock entities
  - Includes entities with mixed data types (String, Int64, Date, Int32, Enum)

### Integration Tests (Requires D365 F&O Environment)
- **`test_entity_validation_odata.py`** - Integration tests against real D365 F&O environments
  - Discovers real composite key entities
  - Tests validation methods against live data
  - Analyzes data type diversity across entities

### Test Runner (Interactive)
- **`run_entity_tests.py`** - Interactive script for comprehensive entity analysis
  - Discovers composite key entities in real environments
  - Tests validation and serialization methods
  - Provides detailed reporting and analysis

## Running Tests

### Unit Tests (Recommended First)
```bash
# Run all unit tests
uv run python -m pytest tests/unit/test_entity_validation_unit.py -v

# Run specific test categories
uv run python -m pytest tests/unit/test_entity_validation_unit.py::TestODataSerializationUnit -v
uv run python -m pytest tests/unit/test_entity_validation_unit.py::TestCompositeKeyScenarios -v
```

### Integration Tests (Requires Environment Setup)
```bash
# Set up environment (required)
export D365FO_SANDBOX_BASE_URL="https://your-d365fo-environment.dynamics.com"
export INTEGRATION_TEST_LEVEL="sandbox"

# Run integration tests
uv run python -m pytest tests/integration/test_entity_validation_odata.py -v

# Run specific integration test
uv run python -m pytest tests/integration/test_entity_validation_odata.py::TestCompositeKeyDiscovery::test_find_entities_with_composite_keys -v -s
```

### Interactive Test Runner
```bash
# Discovery tests only (faster)
python tests/integration/run_entity_tests.py --sandbox --discovery-only

# Full validation tests
python tests/integration/run_entity_tests.py --sandbox

# Live environment (if configured)
python tests/integration/run_entity_tests.py --live
```

## Environment Setup

### Required Environment Variables
```bash
# For sandbox/test environments
export D365FO_SANDBOX_BASE_URL="https://your-test-environment.dynamics.com"

# For live environments (optional)
export D365FO_LIVE_BASE_URL="https://your-live-environment.dynamics.com"

# Test level control
export INTEGRATION_TEST_LEVEL="sandbox"  # or "live" or "all"
```

### Authentication
The tests use Azure Default Credentials, which automatically discover credentials from:
- Environment variables (`AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`)
- Azure CLI (`az login`)
- Managed Identity (when running in Azure)
- Visual Studio Code Azure Account extension
- Other Azure SDK credential sources

## Expected Test Results

### Unit Test Results (Mock Data)
The unit tests use carefully crafted mock entities that demonstrate:

**Composite Key Entity Example:**
```
Entity: CompositeKeyTestEntity
Keys: 5 fields with mixed data types
- CompanyId: String (Edm.String)
- RecordId: Int64 (Edm.Int64)  
- EffectiveDate: Date (Edm.Date)
- Priority: Int32 (Edm.Int32)
- IsActive: Enum (Microsoft.Dynamics.DataEntities.NoYes)
```

**OData Serialization Examples:**
```
String    | "Hello World"        → "Hello%20World" (URL encoded)
Int32     | 42                   → "42" (no quotes)
Real      | 3.14159              → "3.14159" (no quotes)  
Date      | "2023-12-25"         → "2023-12-25" (no quotes)
Enum      | "Yes"                → "Yes" (may be URL encoded)
```

### Integration Test Results (Real Data)
When run against a real D365 F&O environment, the tests typically find:

**Example Composite Key Entities:**
- Financial dimension combinations (CompanyId + DimensionId + Value)
- Time-based records (CompanyId + EntityId + EffectiveDate)  
- Multi-part identifiers (EntityType + RecordId + Version)

**Data Type Diversity:**
- String, Int32, Int64, Real, Date, DateTime, Enum types
- Mixed type composite keys (different data types in same entity)
- D365 F&O specific types (Money, UtcDateTime, VarString, etc.)

## Validation Methods Tested

### Entity Resolution
- `_resolve_entity_name()` - Resolves entity names from collection names, entity set names, or entity names
- `_validate_entity_exists()` - Comprehensive entity existence validation
- `_validate_entity_for_query()` - Fast validation for query operations

### Schema Validation  
- `_validate_entity_schema_and_keys()` - Validates entity schema and key field requirements
- Composite key validation (multiple key fields)
- Key field data type validation
- Mandatory field checking

### OData Serialization
- `_serialize_odata_value()` - Serializes values according to OData protocol
- `_build_validated_key_dict()` - Builds properly serialized key dictionaries
- Support for all D365 F&O ODataXppType values
- Proper URL encoding for different data types

## Key Benefits

### 1. Comprehensive Coverage
- Tests all D365 F&O data types defined in `models.py`
- Covers both simple and composite key scenarios
- Validates edge cases and error conditions

### 2. Real-World Validation
- Discovers actual composite key entities in D365 F&O
- Tests against real entity schemas and data types
- Validates production-ready serialization

### 3. Developer-Friendly
- Unit tests run without environment setup
- Clear error messages and validation feedback
- Interactive runner provides detailed analysis

### 4. Production Ready
- Eliminates "Unknown data type" warnings
- Ensures proper OData URL encoding
- Validates all CRUD operation prerequisites

## Troubleshooting

### Common Issues

**1. Integration Tests Skipped**
```
SKIPPED [sandbox integration tests not enabled]
```
**Solution:** Set `INTEGRATION_TEST_LEVEL=sandbox` environment variable

**2. Connection Failures**
```
Cannot connect to sandbox environment
```
**Solution:** Verify `D365FO_SANDBOX_BASE_URL` and authentication setup

**3. No Composite Key Entities Found**
```
No composite key entities found for testing
```
**Solution:** Try increasing the entity limit in test discovery or use different environment

**4. Authentication Errors**
```
Authentication failed
```
**Solution:** Ensure Azure credentials are configured (run `az login` or set environment variables)

### Debugging Tips

1. **Enable Debug Logging:**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Run Single Test:**
   ```bash
   uv run python -m pytest tests/unit/test_entity_validation_unit.py::TestEntityValidationUnit::test_resolve_entity_name_variations -v -s
   ```

3. **Use Interactive Runner:**
   ```bash
   python tests/integration/run_entity_tests.py --sandbox --discovery-only
   ```

## Integration with CI/CD

### GitHub Actions Example
```yaml
- name: Run Entity Validation Tests
  run: |
    uv run python -m pytest tests/unit/test_entity_validation_unit.py -v
  env:
    PYTHONPATH: ${{ github.workspace }}/src
```

### Environment-Specific Testing
```yaml
- name: Run Integration Tests (Sandbox)
  run: |
    uv run python -m pytest tests/integration/test_entity_validation_odata.py -v
  env:
    D365FO_SANDBOX_BASE_URL: ${{ secrets.D365FO_SANDBOX_URL }}
    INTEGRATION_TEST_LEVEL: sandbox
```

The unit tests provide comprehensive coverage without requiring environment setup, making them ideal for CI/CD pipelines, while integration tests validate against real D365 F&O environments during development and deployment validation.