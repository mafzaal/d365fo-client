# d365fo-client

A comprehensive Python client library for Microsoft Dynamics 365 Finance & Operations (D365 F&O) that provides easy access to OData endpoints, metadata operations, and label management.

## Features

- 🔗 **OData Client**: Full CRUD operations on D365 F&O data entities
- 📊 **Metadata Management**: Download, cache, and search entity/action metadata  
- 🏷️ **Label Operations**: Retrieve and cache multilingual labels with advanced search
- 🔍 **Advanced Querying**: Support for all OData query parameters ($select, $filter, $expand, etc.)
- ⚡ **Action Execution**: Execute both bound and unbound OData actions
- 🔒 **Authentication**: Support for Azure AD authentication (default credentials or client secrets)
- 💾 **Intelligent Caching**: Built-in caching for metadata and labels to improve performance
- 🌐 **Async/Await**: Modern async/await pattern for optimal performance
- 📝 **Type Hints**: Full type annotation support for better IDE experience

## Installation

```bash
# Install from PyPI (when published)
pip install d365fo-client

# Or install from source
git clone https://github.com/mafzaal/d365fo-client.git
cd d365fo-client
pip install -e .
```

## Quick Start

### Basic Usage

```python
import asyncio
from d365fo_client import FOClient, FOClientConfig

async def main():
    # Simple configuration
    config = FOClientConfig(
        base_url="https://your-fo-environment.dynamics.com",
        use_default_credentials=True  # Uses Azure Default Credential
    )
    
    async with FOClient(config) as client:
        # Test connection
        if await client.test_connection():
            print("✅ Connected successfully!")
        
        # Download metadata
        await client.download_metadata()
        
        # Search for entities
        customer_entities = client.search_entities("customer")
        print(f"Found {len(customer_entities)} customer entities")
        
        # Get customers with query options
        from d365fo_client import QueryOptions
        options = QueryOptions(
            select=["CustomerAccount", "Name", "SalesCurrencyCode"],
            top=10,
            orderby=["Name"]
        )
        
        customers = await client.get_entities("Customers", options)
        print(f"Retrieved {len(customers['value'])} customers")

if __name__ == "__main__":
    asyncio.run(main())
```

### Using Convenience Function

```python
from d365fo_client import create_client

# Quick client creation
async with create_client("https://your-fo-environment.dynamics.com") as client:
    customers = await client.get_entities("Customers", top=5)
```

## Configuration

### Authentication Options

```python
from d365fo_client import FOClientConfig

# Option 1: Default Azure credentials (recommended)
config = FOClientConfig(
    base_url="https://your-fo-environment.dynamics.com",
    use_default_credentials=True
)

# Option 2: Client credentials
config = FOClientConfig(
    base_url="https://your-fo-environment.dynamics.com",
    client_id="your-client-id",
    client_secret="your-client-secret", 
    tenant_id="your-tenant-id",
    use_default_credentials=False
)

# Option 3: With custom settings
config = FOClientConfig(
    base_url="https://your-fo-environment.dynamics.com",
    use_default_credentials=True,
    verify_ssl=False,  # For development environments
    timeout=60,  # Request timeout in seconds
    metadata_cache_dir="./my_cache",  # Custom cache directory
    use_label_cache=True,  # Enable label caching
    label_cache_expiry_minutes=120  # Cache for 2 hours
)
```

## Core Operations

### CRUD Operations

```python
async with FOClient(config) as client:
    # CREATE - Create new customer
    new_customer = {
        "CustomerAccount": "US-999",
        "Name": "Test Customer",
        "SalesCurrencyCode": "USD"
    }
    created = await client.create_entity("Customers", new_customer)
    
    # READ - Get single customer
    customer = await client.get_entity("Customers", "US-001")
    
    # UPDATE - Update customer
    updates = {"Name": "Updated Customer Name"}
    updated = await client.update_entity("Customers", "US-001", updates)
    
    # DELETE - Delete customer
    success = await client.delete_entity("Customers", "US-999")
```

### Advanced Querying

```python
from d365fo_client import QueryOptions

# Complex query with multiple options
options = QueryOptions(
    select=["CustomerAccount", "Name", "SalesCurrencyCode", "CustomerGroupId"],
    filter="SalesCurrencyCode eq 'USD' and contains(Name, 'Corp')",
    expand=["CustomerGroup"],
    orderby=["Name desc", "CustomerAccount"],
    top=50,
    skip=10,
    count=True
)

result = await client.get_entities("Customers", options)
print(f"Total count: {result.get('@odata.count')}")
```

### Action Execution

```python
# Unbound action
result = await client.call_action("calculateTax", {
    "amount": 1000.00,
    "taxGroup": "STANDARD"
})

# Bound action on specific entity
result = await client.call_action(
    "calculateBalance",
    parameters={"asOfDate": "2024-12-31"},
    entity_name="Customers", 
    entity_key="US-001"
)
```

### Metadata Operations

```python
# Download and cache metadata
await client.download_metadata(force_refresh=True)

# Search entities
sales_entities = client.search_entities("sales")
print("Sales-related entities:", sales_entities)

# Get detailed entity information
entity_info = client.get_entity_info("Customers")
if entity_info:
    print(f"Entity: {entity_info.name}")
    print(f"Keys: {entity_info.keys}")
    print(f"Properties: {len(entity_info.properties)}")

# Search actions
calc_actions = client.search_actions("calculate")
print("Calculation actions:", calc_actions)
```

### Label Operations

```python
# Get specific label
label_text = await client.get_label_text("@SYS13342")
print(f"Label text: {label_text}")

# Get multiple labels
labels = await client.get_labels_batch([
    "@SYS13342", "@SYS9490", "@GLS63332"
])
for label_id, text in labels.items():
    print(f"{label_id}: {text}")

```
# Enhanced entity info with resolved labels
entity_info = await client.get_entity_info_with_labels("Customers")
if entity_info.label_text:
    print(f"Entity display name: {entity_info.label_text}")

for prop in entity_info.enhanced_properties[:5]:
    if prop.label_text:
        print(f"{prop.name}: {prop.label_text}")
```

## Error Handling

```python
from d365fo_client import FOClientError, EntityError, AuthenticationError

try:
    async with FOClient(config) as client:
        customer = await client.get_entity("Customers", "NON-EXISTENT")
except EntityError as e:
    print(f"Entity operation failed: {e}")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except FOClientError as e:
    print(f"General client error: {e}")
```

## Development

### Setting up Development Environment

```bash
# Clone the repository
git clone https://github.com/mafzaal/d365fo-client.git
cd d365fo-client

# Install with development dependencies
uv sync --dev

# Run tests
uv run pytest

# Format code
uv run black .
uv run isort .

# Type checking
uv run mypy src/
```

### Project Structure

```
d365fo-client/
├── src/
│   └── d365fo_client/
│       ├── __init__.py          # Public API exports
│       ├── client.py            # Main FOClient class
│       ├── models.py            # Data models and configurations
│       ├── auth.py              # Authentication management
│       ├── session.py           # HTTP session management
│       ├── metadata.py          # Metadata operations
│       ├── cache.py             # Label caching
│       ├── crud.py              # CRUD operations
│       ├── labels.py            # Label operations
│       ├── query.py             # OData query utilities
│       ├── exceptions.py        # Custom exceptions
│       └── main.py              # CLI entry point
├── tests/                       # Test files
├── docs/                        # Documentation
├── pyproject.toml               # Project configuration
└── README.md                    # This file
```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `base_url` | str | Required | D365 F&O base URL |
| `client_id` | str | None | Azure AD client ID |
| `client_secret` | str | None | Azure AD client secret |
| `tenant_id` | str | None | Azure AD tenant ID |
| `use_default_credentials` | bool | True | Use Azure Default Credential |
| `verify_ssl` | bool | False | Verify SSL certificates |
| `timeout` | int | 30 | Request timeout in seconds |
| `metadata_cache_dir` | str | "./metadata_cache" | Metadata cache directory |
| `use_label_cache` | bool | True | Enable label caching |
| `label_cache_expiry_minutes` | int | 60 | Label cache expiry time |

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`uv run pytest`)
5. Format code (`uv run black . && uv run isort .`)
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes and version history.

## Support

- 📧 Email: mo@thedataguy.pro
- 🐛 Issues: [GitHub Issues](https://github.com/mafzaal/d365fo-client/issues)
- 📖 Documentation: [Read the Docs](https://d365fo-client.readthedocs.io)

## Related Projects

- [Microsoft Dynamics 365](https://dynamics.microsoft.com/)
- [OData](https://www.odata.org/)
- [Azure Identity](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/identity/azure-identity)
