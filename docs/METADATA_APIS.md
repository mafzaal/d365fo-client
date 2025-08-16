# Metadata APIs Implementation

This document describes the implementation of the three new metadata API endpoints for the D365 F&O client:

1. **DataEntities** - Information about data entities
2. **PublicEntities** - Detailed public entity information with properties
3. **PublicEnumerations** - Enumeration definitions with values

## API Endpoints

The metadata APIs are available at the following endpoints:

```
GET {base_url}/Metadata/DataEntities
GET {base_url}/Metadata/PublicEntities  
GET {base_url}/Metadata/PublicEnumerations
```

## Data Structures

### DataEntityInfo
Information about data entities from the DataEntities endpoint:

```python
@dataclass
class DataEntityInfo:
    name: str                           # Entity name
    public_entity_name: str             # Public entity name
    public_collection_name: str         # Collection name
    label_id: Optional[str] = None      # Label ID
    label_text: Optional[str] = None    # Resolved label text
    data_service_enabled: bool = True   # Data service enabled
    data_management_enabled: bool = True # Data management enabled
    entity_category: Optional[str] = None # Category (Master, Transaction, etc.)
    is_read_only: bool = False          # Read-only status
```

### PublicEntityInfo
Detailed information about public entities:

```python
@dataclass
class PublicEntityInfo:
    name: str                           # Entity name
    entity_set_name: str                # Entity set name
    label_id: Optional[str] = None      # Label ID
    label_text: Optional[str] = None    # Resolved label text
    is_read_only: bool = False          # Read-only status
    configuration_enabled: bool = True  # Configuration enabled
    properties: List[PublicEntityPropertyInfo] = None # Detailed properties
    navigation_properties: List[Dict[str, Any]] = None # Navigation properties
    property_groups: List[Dict[str, Any]] = None # Property groups
    actions: List[str] = None           # Available actions
```

### EnumerationInfo
Information about enumerations:

```python
@dataclass
class EnumerationInfo:
    name: str                           # Enumeration name
    label_id: Optional[str] = None      # Label ID
    label_text: Optional[str] = None    # Resolved label text
    members: List[EnumerationMemberInfo] = None # Enumeration members
```

## Client Methods

### DataEntities API

#### get_data_entities(options: Optional[QueryOptions] = None)
Get data entities from DataEntities metadata endpoint.

```python
# Get first 10 data entities
options = QueryOptions(top=10)
entities = await client.get_data_entities(options)
```

#### search_data_entities(pattern, entity_category, data_service_enabled, data_management_enabled, is_read_only)
Search data entities with filtering.

```python
# Search for customer-related entities
entities = await client.search_data_entities("customer")

# Search for Master category entities
entities = await client.search_data_entities("", entity_category="Master")

# Search for read-only transaction entities
entities = await client.search_data_entities(
    "", 
    entity_category="Transaction", 
    is_read_only=True
)
```

#### get_data_entity_info(entity_name, resolve_labels=True, language="en-US")
Get detailed information about a specific data entity.

```python
entity = await client.get_data_entity_info("CustomerEntity")
print(f"Entity: {entity.name}")
print(f"Label: {entity.label_text}")
print(f"Category: {entity.entity_category}")
```

### PublicEntities API

#### get_public_entities(options: Optional[QueryOptions] = None)
Get public entities from PublicEntities metadata endpoint.

```python
# Get first 10 public entities
options = QueryOptions(top=10)
entities = await client.get_public_entities(options)
```

#### search_public_entities(pattern, is_read_only, configuration_enabled)
Search public entities with filtering.

```python
# Search for customer-related entities
entities = await client.search_public_entities("customer")

# Search for read-only entities
entities = await client.search_public_entities("", is_read_only=True)
```

#### get_public_entity_info(entity_name, resolve_labels=True, language="en-US")
Get detailed information about a specific public entity.

```python
entity = await client.get_public_entity_info("Customer")
print(f"Entity: {entity.name}")
print(f"Entity Set: {entity.entity_set_name}")
print(f"Properties: {len(entity.properties)}")

# Access properties
for prop in entity.properties:
    if prop.is_key:
        print(f"Key: {prop.name} ({prop.type_name})")
```

### PublicEnumerations API

#### get_public_enumerations(options: Optional[QueryOptions] = None)
Get public enumerations from PublicEnumerations metadata endpoint.

```python
# Get first 10 enumerations
options = QueryOptions(top=10)
enums = await client.get_public_enumerations(options)
```

#### search_public_enumerations(pattern)
Search public enumerations with filtering.

```python
# Search for account-related enumerations
enums = await client.search_public_enumerations("account")
```

#### get_public_enumeration_info(enumeration_name, resolve_labels=True, language="en-US")
Get detailed information about a specific enumeration.

```python
enum = await client.get_public_enumeration_info("ABC")
print(f"Enumeration: {enum.name}")
print(f"Label: {enum.label_text}")

# Access values
for member in enum.members:
    print(f"{member.name} = {member.value}: {member.label_text}")
```

## Complete Example

```python
import asyncio
from d365fo_client import FOClient, FOClientConfig, QueryOptions

async def metadata_example():
    config = FOClientConfig(
        base_url="https://your-environment.dynamics.com",
        use_default_credentials=True
    )
    
    async with FOClient(config) as client:
        # Search for customer entities
        print("=== Data Entities ===")
        data_entities = await client.search_data_entities("customer")
        print(f"Found {len(data_entities)} customer data entities")
        
        # Get public entity details
        print("\n=== Public Entity Details ===")
        customer_entity = await client.get_public_entity_info("Customer")
        if customer_entity:
            print(f"Entity: {customer_entity.name}")
            print(f"Properties: {len(customer_entity.properties)}")
            
            # Show key properties
            keys = [p.name for p in customer_entity.properties if p.is_key]
            print(f"Keys: {', '.join(keys)}")
        
        # Get enumeration details
        print("\n=== Enumeration Details ===")
        abc_enum = await client.get_public_enumeration_info("ABC")
        if abc_enum:
            print(f"Enumeration: {abc_enum.name}")
            for member in abc_enum.members:
                print(f"  {member.name} = {member.value}")
        
        # Advanced filtering
        print("\n=== Advanced Filtering ===")
        
        # Master data entities
        masters = await client.search_data_entities("", entity_category="Master")
        print(f"Master entities: {len(masters)}")
        
        # Read-only entities
        readonly = await client.search_public_entities("", is_read_only=True)
        print(f"Read-only entities: {len(readonly)}")
        
        # Account-related enumerations
        account_enums = await client.search_public_enumerations("account")
        print(f"Account enumerations: {len(account_enums)}")

if __name__ == "__main__":
    asyncio.run(metadata_example())
```

## Entity Categories

The DataEntities endpoint supports filtering by entity category:

- **Master** - Master data entities
- **Transaction** - Transaction entities  
- **Reference** - Reference data entities
- **Parameters** - Parameter entities
- **Configuration** - Configuration entities
- **Document** - Document entities

## Label Resolution

All metadata APIs support automatic label resolution when `resolve_labels=True` (default):

```python
# Labels are automatically resolved
entity = await client.get_public_entity_info("Customer")
print(entity.label_text)  # "Customers" (resolved from @SYS...)

# Access property labels
for prop in entity.properties:
    print(f"{prop.name}: {prop.label_text}")
```

## Performance Considerations

- Use query options to limit results when getting all entities/enumerations
- Search methods only return basic information for better performance
- Use specific info methods to get full details including properties/members
- Label resolution makes additional API calls - disable if not needed

## Error Handling

All methods can raise exceptions for:
- Network connectivity issues
- Authentication failures
- Invalid entity/enumeration names (returns None instead of exception)
- OData query syntax errors

```python
try:
    entity = await client.get_public_entity_info("NonExistentEntity")
    if entity is None:
        print("Entity not found")
except Exception as e:
    print(f"Error: {e}")
```