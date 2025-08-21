# D365 F&O Metadata Scripts

This folder contains utility scripts for working with Microsoft Dynamics 365 Finance & Operations metadata using the d365fo-client package.

## Scripts Overview

### Data Entities
- **`search_data_entities.ps1`** - Search for data entities by pattern
- **`get_data_entity_schema.ps1`** - Get detailed schema information for a specific entity

### Enumerations
- **`search_enums.py`** - Search for enumerations by pattern  
- **`get_enumeration_info.py`** - Get detailed information for a specific enumeration

### Actions
- **`search_actions.ps1`** - Search for actions by pattern
- **`get_action_info.py`** - Get detailed information for a specific action

## Prerequisites

1. **d365fo-client package** installed and configured
2. **PowerShell** (for .ps1 scripts)
3. **Python 3.13+** (for .py scripts)
4. **uv** package manager
5. **D365 F&O environment access** with proper authentication

## Configuration

### Environment Variables
Set these environment variables or use command-line parameters:

```bash
# Required
export D365FO_BASE_URL="https://your-environment.dynamics.com"

# Optional (for explicit authentication)
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"  
export AZURE_TENANT_ID="your-tenant-id"
```

### Authentication
The scripts support multiple authentication methods:
1. **Default Credentials** (recommended) - Uses Azure CLI, Managed Identity, etc.
2. **Environment Variables** - Uses explicit client credentials
3. **Command-line Parameters** - Override via `--base-url` parameter

## Usage Examples

### Search Data Entities

```powershell
# Basic search
.\search_data_entities.ps1 -Pattern "customer"

# Advanced search with options
.\search_data_entities.ps1 -Pattern ".*sales.*" -Output json -Limit 10

# Use specific environment
.\search_data_entities.ps1 -Pattern "inventory" -BaseUrl "https://myenv.dynamics.com" -Verbose
```

### Get Entity Schema

```powershell
# Basic schema info
.\get_data_entity_schema.ps1 -EntityName "CustomersV3"

# Detailed schema with all information
.\get_data_entity_schema.ps1 -EntityName "SalesOrderHeaders" -Properties -Keys -Labels -Output json
```

### Search Enumerations

```bash
# Basic enumeration search
python search_enums.py "status"

# Advanced search with formatting
python search_enums.py ".*Type.*" --output json --limit 5 --verbose
```

### Get Enumeration Details

```bash
# Get enumeration details
python get_enumeration_info.py "CustVendorBlocked"

# Get details without labels (faster)
python get_enumeration_info.py "ItemType" --no-labels --output csv
```

### Search Actions

```powershell
# List all actions
.\search_actions.ps1

# Search by pattern
.\search_actions.ps1 -Pattern "post" -Output json

# Filter by entity
.\search_actions.ps1 -Entity "CustomersV3" -Verbose
```

### Get Action Details

```bash
# Get action information
python get_action_info.py "Microsoft.Dynamics.DataEntities.GetKeys"

# Detailed action info
python get_action_info.py "SalesOrderHeadersV2_PostSalesOrder" --output json --verbose
```

## Output Formats

All scripts support multiple output formats:

- **`table`** (default) - Human-readable table format
- **`json`** - JSON format for programmatic use
- **`csv`** - Comma-separated values for Excel/data analysis
- **`yaml`** - YAML format (where supported)
- **`list`** - Simple list format

## Common Parameters

### PowerShell Scripts (.ps1)
- `-Pattern` - Search pattern (regex supported)
- `-Output` - Output format (table, json, csv, yaml)
- `-BaseUrl` - D365 F&O environment URL
- `-Profile` - Configuration profile to use
- `-Verbose` - Enable verbose output

### Python Scripts (.py)
- `pattern` or `name` - Search pattern or specific name
- `--output, -o` - Output format (table, json, csv, list)
- `--base-url` - D365 F&O environment URL  
- `--profile` - Configuration profile to use
- `--verbose, -v` - Enable verbose output

## Error Handling

All scripts include comprehensive error handling:
- **Authentication errors** - Clear messages about credential issues
- **Network errors** - Timeout and connection issue handling
- **API errors** - D365 F&O specific error messages
- **Parameter validation** - Input validation with helpful messages

## Performance Considerations

- **Caching** - Scripts leverage metadata and label caching for better performance
- **Limits** - Use `--limit` parameter for large result sets
- **Parallel execution** - Scripts can be run concurrently for different operations

## Integration Examples

### Batch Processing
```bash
# Get schema for multiple entities
entities=("CustomersV3" "VendorsV2" "ItemsV2")
for entity in "${entities[@]}"; do
    python get_data_entity_schema.py "$entity" --output json > "${entity}_schema.json"
done
```

### Pipeline Integration
```powershell
# Search and get details in one pipeline
$entities = .\search_data_entities.ps1 -Pattern "customer" -Output json | ConvertFrom-Json
foreach ($entity in $entities) {
    .\get_data_entity_schema.ps1 -EntityName $entity.name -Output json
}
```

## Troubleshooting

### Common Issues

1. **"No module named d365fo_client"**
   - Ensure you're running from the project root
   - Verify d365fo-client is installed: `uv run python -c "import d365fo_client"`

2. **Authentication failures**
   - Check environment variables are set correctly
   - Verify Azure credentials: `az account show`
   - Try explicit credentials with `--base-url` parameter

3. **Connection timeouts**
   - Check D365 F&O environment URL is correct
   - Verify network connectivity
   - Use `--verbose` flag for detailed error information

4. **PowerShell execution policy**
   - Run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

### Getting Help

- Use `--help` or `-h` with any script for detailed usage information
- Check the main project documentation in the `docs/` folder
- Review integration test examples in `tests/integration/`

## Contributing

When adding new scripts:
1. Follow the existing naming convention
2. Include comprehensive help documentation
3. Support all common output formats
4. Add error handling and validation
5. Update this README with usage examples