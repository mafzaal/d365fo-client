---
mode: 'agent'
description: Implement OData action method with proper typing and metadata analysis
---

# OData Action Implementation Prompt

You are a Python developer working on the d365fo-client package. Your task is to implement a method for calling an OData action in Microsoft Dynamics 365 Finance & Operations. Follow these steps systematically:

## Step 1: Search and Analyze Action Metadata

First, search the metadata to find details about the OData action:

```python
# Search for the action in the metadata
action_info = client.get_action_info("ActionName")

# If not found in cached metadata, search in PublicEntities
entity_info = await client.get_public_entity_info("EntityName")
if entity_info and entity_info.actions:
    action_info = next((a for a in entity_info.actions if a.name == "ActionName"), None)
```

## Step 2: Determine Action Binding Type

Analyze if the action is:
- **Static Action**: Not bound to any entity (`is_bound=False` or `binding_kind=""`)
- **Entity Bound**: Bound to a single entity instance (`binding_kind="Entity"`)
- **Collection Bound**: Bound to an entity set (`binding_kind="Collection"`)

```python
if action_info.binding_kind == "Entity":
    # Entity-bound action - requires entity key
    binding_type = "entity"
elif action_info.binding_kind == "Collection":
    # Collection-bound action - operates on entity set
    binding_type = "collection"
else:
    # Static action - no binding required
    binding_type = "static"
```

## Step 3: Analyze Parameters and Return Type

Extract parameter information and return type:

```python
# Analyze parameters
parameters = []
for param in action_info.parameters:
    param_info = {
        'name': param.name,
        'type': param.type.type_name,
        'is_collection': param.type.is_collection,
        'is_optional': False  # Determine from metadata
    }
    parameters.append(param_info)

# Analyze return type
return_type = None
if action_info.return_type:
    return_type = {
        'type': action_info.return_type.type_name,
        'is_collection': action_info.return_type.is_collection
    }
```

## Step 4: Define Return Type Models (if needed)

If the return type is a complex type, create a dataclass model:

```python
from dataclasses import dataclass
from typing import List, Optional, Any

@dataclass
class ActionResultModel:
    """Result model for {ActionName} action"""
    # Define fields based on the complex type structure
    field1: str
    field2: Optional[int] = None
    field3: List[str] = None
    
    def __post_init__(self):
        if self.field3 is None:
            self.field3 = []
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionResultModel':
        """Create model from dictionary response"""
        return cls(
            field1=data.get('Field1', ''),
            field2=data.get('Field2'),
            field3=data.get('Field3', [])
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            'Field1': self.field1,
            'Field2': self.field2,
            'Field3': self.field3
        }
```

## Step 5: Implement the Action Method

Create a method in the appropriate class based on binding type:

### For Static Actions (add to FOClient):

```python
async def action_name(self, param1: str, param2: Optional[int] = None) -> ActionResultModel:
    """Call {ActionName} static action
    
    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2 (optional)
        
    Returns:
        ActionResultModel: The action result
        
    Raises:
        FOClientError: If the action call fails
    """
    parameters = {
        'Param1': param1
    }
    if param2 is not None:
        parameters['Param2'] = param2
    
    try:
        result = await self.call_action("ActionName", parameters)
        
        # Handle different return types
        if isinstance(result, dict):
            return ActionResultModel.from_dict(result)
        elif result is None or result == {"success": True}:
            # Void return or success indicator
            return None
        else:
            # Simple value return
            return result
            
    except Exception as e:
        raise FOClientError(f"Failed to call action ActionName: {e}")
```

### For Entity-Bound Actions:

```python
async def action_name(self, entity_key: str, param1: str, 
                     param2: Optional[int] = None) -> ActionResultModel:
    """Call {ActionName} action on specific entity
    
    Args:
        entity_key: The key of the entity to call action on
        param1: Description of parameter 1
        param2: Description of parameter 2 (optional)
        
    Returns:
        ActionResultModel: The action result
        
    Raises:
        FOClientError: If the action call fails
    """
    parameters = {
        'Param1': param1
    }
    if param2 is not None:
        parameters['Param2'] = param2
    
    try:
        result = await self.call_action(
            "ActionName", 
            parameters, 
            entity_name="EntityName",
            entity_key=entity_key
        )
        
        if isinstance(result, dict):
            return ActionResultModel.from_dict(result)
        else:
            return result
            
    except Exception as e:
        raise FOClientError(f"Failed to call action ActionName on entity {entity_key}: {e}")
```

### For Collection-Bound Actions:

```python
async def action_name(self, param1: str, 
                     param2: Optional[int] = None) -> List[ActionResultModel]:
    """Call {ActionName} action on entity collection
    
    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2 (optional)
        
    Returns:
        List[ActionResultModel]: The action results
        
    Raises:
        FOClientError: If the action call fails
    """
    parameters = {
        'Param1': param1
    }
    if param2 is not None:
        parameters['Param2'] = param2
    
    try:
        result = await self.call_action(
            "ActionName", 
            parameters, 
            entity_name="EntityName"
        )
        
        if isinstance(result, dict) and 'value' in result:
            # Collection response
            return [ActionResultModel.from_dict(item) for item in result['value']]
        elif isinstance(result, list):
            return [ActionResultModel.from_dict(item) for item in result]
        else:
            return [ActionResultModel.from_dict(result)] if result else []
            
    except Exception as e:
        raise FOClientError(f"Failed to call action ActionName on entity collection: {e}")
```

## Step 6: Add Type Hints and Documentation

Ensure proper type hints and comprehensive docstrings:

```python
from typing import Union, List, Optional, Dict, Any
from .models import ActionResultModel
from .exceptions import FOClientError
```

## Step 7: Add Unit Tests

Create tests for the action method:

```python
import pytest
from unittest.mock import AsyncMock, patch
from d365fo_client import FOClient, FOClientConfig
from d365fo_client.models import ActionResultModel

@pytest.mark.asyncio
async def test_action_name_success():
    """Test successful action call"""
    config = FOClientConfig(base_url="https://test.dynamics.com")
    
    with patch.object(FOClient, 'call_action') as mock_call:
        mock_call.return_value = {
            'Field1': 'test_value',
            'Field2': 123,
            'Field3': ['item1', 'item2']
        }
        
        async with FOClient(config) as client:
            result = await client.action_name("param1_value", 456)
            
            assert isinstance(result, ActionResultModel)
            assert result.field1 == 'test_value'
            assert result.field2 == 123
            assert result.field3 == ['item1', 'item2']
            
            mock_call.assert_called_once_with(
                "ActionName",
                {'Param1': 'param1_value', 'Param2': 456}
            )

@pytest.mark.asyncio
async def test_action_name_error():
    """Test action call error handling"""
    config = FOClientConfig(base_url="https://test.dynamics.com")
    
    with patch.object(FOClient, 'call_action') as mock_call:
        mock_call.side_effect = Exception("Action failed")
        
        async with FOClient(config) as client:
            with pytest.raises(FOClientError, match="Failed to call action ActionName"):
                await client.action_name("param1_value")
```

## Step 8: Update Documentation

Add the new action method to the class documentation and create usage examples:

```python
# Example usage
async def example_usage():
    config = FOClientConfig(base_url="https://your-d365.dynamics.com")
    
    async with FOClient(config) as client:
        # For static actions
        result = await client.action_name("value1", 123)
        
        # For entity-bound actions
        result = await client.action_name("entity_key_value", "value1", 123)
        
        # For collection-bound actions
        results = await client.action_name("value1", 123)
        
        print(f"Action completed: {result}")
```

## Implementation Guidelines

1. **Error Handling**: Always wrap action calls in try-catch blocks
2. **Type Safety**: Use proper type hints for all parameters and return types
3. **Documentation**: Provide clear docstrings with parameter descriptions
4. **Validation**: Validate required parameters before making the call
5. **Consistency**: Follow existing patterns in the codebase
6. **Testing**: Write comprehensive unit tests for the new method
7. **Logging**: Add appropriate logging for debugging purposes

## Example: Complete Implementation

Here's a complete example for a hypothetical "ValidateCustomer" action:

```python
@dataclass
class ValidationResult:
    """Result of customer validation"""
    is_valid: bool
    validation_errors: List[str]
    customer_id: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValidationResult':
        return cls(
            is_valid=data.get('IsValid', False),
            validation_errors=data.get('ValidationErrors', []),
            customer_id=data.get('CustomerId', '')
        )

# In FOClient class
async def validate_customer(self, customer_account: str, 
                          validate_credit: bool = True) -> ValidationResult:
    """Validate customer account and credit status
    
    Args:
        customer_account: Customer account number to validate
        validate_credit: Whether to include credit validation
        
    Returns:
        ValidationResult: Validation results
        
    Raises:
        FOClientError: If validation fails or customer not found
    """
    parameters = {
        'CustomerAccount': customer_account,
        'ValidateCredit': validate_credit
    }
    
    try:
        result = await self.call_action("ValidateCustomer", parameters)
        return ValidationResult.from_dict(result)
    except Exception as e:
        raise FOClientError(f"Failed to validate customer {customer_account}: {e}")
```

This prompt provides a systematic approach to implementing OData actions with proper metadata analysis, type safety, and comprehensive error handling.
