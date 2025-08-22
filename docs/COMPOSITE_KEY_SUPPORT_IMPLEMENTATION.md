# Composite Key Support Implementation

## Issue Summary

The MCP server's `d365fo_update_entity_record` tool was failing when trying to update records with composite keys. The error showed:

```
PATCH CustomersV3({'dataAreaId': 'usmf', 'CustomerAccount': 'MAFZAAL001'}) failed: 404 - {"Message":"No HTTP resource was found that matches the request URI 'https://usnconeboxax1aos.cloud.onebox.dynamics.com/data/CustomersV3('{'dataAreaId': 'usmf', 'CustomerAccount': 'MAFZAAL001'}')'. No route data was found for this request."}
```

The problem was that composite keys (dictionaries) were being converted to string representations rather than being properly formatted for OData URLs.

## Root Cause

1. **MCP Models Support**: The MCP models already supported `Union[str, Dict[str, Any]]` for keys
2. **QueryBuilder Limitation**: The `QueryBuilder.encode_key()` method only handled string keys
3. **Missing URL Formatting**: The `QueryBuilder.build_entity_url()` method didn't properly format composite keys for OData
4. **Missing Client Method**: The MCP tools called `client.get_entity_by_key()` which didn't exist

## Solution Implementation

### 1. Updated `QueryBuilder.encode_key()` Method

Enhanced to handle both simple and composite keys:

```python
@staticmethod
def encode_key(key: Union[str, Dict[str, Any]]) -> str:
    if isinstance(key, dict):
        # Format composite key: key1=value1,key2=value2
        key_parts = []
        for key_name, key_value in key.items():
            encoded_value = quote(str(key_value), safe='')
            key_parts.append(f"{key_name}='{encoded_value}'")
        return ",".join(key_parts)
    else:
        # Simple string key
        return quote(str(key), safe='')
```

### 2. Updated `QueryBuilder.build_entity_url()` Method

Enhanced to properly format URLs for both simple and composite keys:

```python
@staticmethod
def build_entity_url(base_url: str, entity_name: str, key: Optional[Union[str, Dict[str, Any]]] = None) -> str:
    base = f"{base_url.rstrip('/')}/data/{entity_name}"
    if key:
        encoded_key = QueryBuilder.encode_key(key)
        if isinstance(key, dict):
            # For composite keys, don't wrap in additional quotes
            return f"{base}({encoded_key})"
        else:
            # For simple string keys, wrap in quotes
            return f"{base}('{encoded_key}')"
    return base
```

### 3. Updated CRUD Operations

Updated all CRUD methods to support `Union[str, Dict[str, Any]]` for keys:

- `CrudOperations.get_entity()`
- `CrudOperations.update_entity()`
- `CrudOperations.delete_entity()`
- `CrudOperations.call_action()`

### 4. Updated D365FOClient Methods

Updated client methods to support composite keys:

- `D365FOClient.get_entity()`
- `D365FOClient.update_entity()`
- `D365FOClient.delete_entity()`
- `D365FOClient.call_action()`
- `D365FOClient.get_entity_url()`
- `D365FOClient.get_action_url()`

### 5. Added Missing `get_entity_by_key()` Method

Added the missing method that MCP tools were calling:

```python
async def get_entity_by_key(self, entity_name: str, key: Union[str, Dict[str, Any]], 
                           select: Optional[List[str]] = None, 
                           expand: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    try:
        options = QueryOptions(select=select, expand=expand) if select or expand else None
        return await self.crud_ops.get_entity(entity_name, key, options)
    except Exception as e:
        # If the entity is not found, return None instead of raising exception
        if "404" in str(e):
            return None
        raise
```

## Key Format Examples

### Simple Key
- Input: `"CUST001"`
- URL: `/data/CustomersV3('CUST001')`

### Composite Key
- Input: `{"dataAreaId": "usmf", "CustomerAccount": "MAFZAAL001"}`
- URL: `/data/CustomersV3(dataAreaId='usmf',CustomerAccount='MAFZAAL001')`

### Complex Composite Key
- Input: `{"dataAreaId": "us/mf", "CustomerAccount": "CUST & CO"}`
- URL: `/data/CustomersV3(dataAreaId='us%2Fmf',CustomerAccount='CUST%20%26%20CO')`

## Testing

### Unit Tests Added

Created comprehensive test suite in `tests/unit/test_composite_keys.py`:

- ✅ Simple key encoding
- ✅ Composite key encoding
- ✅ Special character handling
- ✅ URL building for both key types
- ✅ Action URL building
- ✅ Real-world error case validation
- ✅ Multiple field composite keys

### Test Results

All 13 composite key tests pass:

```
tests/unit/test_composite_keys.py::TestCompositeKeyHandling::test_encode_simple_key PASSED
tests/unit/test_composite_keys.py::TestCompositeKeyHandling::test_encode_composite_key PASSED
tests/unit/test_composite_keys.py::TestCompositeKeyHandling::test_build_entity_url_composite_key PASSED
tests/unit/test_composite_keys.py::TestCompositeKeyHandling::test_real_world_composite_key_case PASSED
...
```

## Backward Compatibility

The changes are fully backward compatible:

- ✅ Existing string keys continue to work unchanged
- ✅ All existing APIs maintain their signatures (now with enhanced type support)
- ✅ No breaking changes to MCP tool interfaces
- ✅ All existing tests continue to pass

## Files Modified

1. **Core Libraries**:
   - `src/d365fo_client/query.py` - Enhanced key encoding and URL building
   - `src/d365fo_client/crud.py` - Updated CRUD operations for composite keys
   - `src/d365fo_client/client.py` - Updated client methods and added missing method

2. **Type Annotations**:
   - Added `Union[str, Dict[str, Any]]` imports where needed
   - Updated method signatures throughout the stack

3. **Tests**:
   - `tests/unit/test_composite_keys.py` - Comprehensive test suite

## Impact on MCP Tools

The fix directly resolves the MCP server error:

- ✅ `d365fo_update_entity_record` now works with composite keys
- ✅ `d365fo_get_entity_record` now works with composite keys
- ✅ `d365fo_delete_entity_record` now works with composite keys
- ✅ `d365fo_call_action` now works with composite entity keys

## Example Usage

### Before (Failed)
```json
{
  "data": {"PrimaryContactPhone": "609-819-5700"},
  "entityName": "CustomersV3",
  "key": {"dataAreaId": "usmf", "CustomerAccount": "MAFZAAL001"},
  "returnRecord": true
}
```
**Result**: 404 Error - Invalid URL format

### After (Works)
```json
{
  "data": {"PrimaryContactPhone": "609-819-5700"},
  "entityName": "CustomersV3", 
  "key": {"dataAreaId": "usmf", "CustomerAccount": "MAFZAAL001"},
  "returnRecord": true
}
```
**Result**: Successful update with proper URL: `/data/CustomersV3(dataAreaId='usmf',CustomerAccount='MAFZAAL001')`

## Conclusion

This implementation provides complete support for D365 F&O composite keys across the entire d365fo-client library, resolving the MCP server error while maintaining full backward compatibility and adding comprehensive test coverage.