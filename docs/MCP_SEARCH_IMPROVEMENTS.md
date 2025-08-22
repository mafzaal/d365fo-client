# MCP Search Tool Improvements

## Overview
Enhanced the `d365fo_search_entities` MCP tool to provide better guidance and results when searching for D365 F&O data entities, particularly for customer groups and other specific entity types. Added FTS5 full-text search fallback for improved discovery.

## Issues Identified

### 1. Poor Search Guidance
- AI assistants were using overly specific regex patterns that didn't match D365 F&O naming conventions
- No examples provided of actual D365 F&O entity naming patterns
- Tool descriptions were too generic and didn't help users understand D365 F&O specifics

### 2. No Fallback Strategies
- When searches returned no results, users had no guidance on alternative approaches
- No suggestions provided for broader or alternative search patterns
- No intelligent search alternatives like full-text search

### 3. Limited Error Context
- Empty results provided no helpful suggestions
- No indication of what might work better

## Improvements Made

### 1. Enhanced Tool Description
**Before:**
```
"Search for D365 F&O data entities by name, pattern, or properties. Use this to discover available entities for data operations."
```

**After:**
```
"Search for D365 F&O data entities by name, pattern, or properties. D365 F&O entity names follow specific patterns - try multiple search strategies for best results. For customer groups, try patterns like 'Customer.*Group', 'Cust.*Group', '.*CustomerGroup.*', or search for 'Group' alone to find all group-related entities."
```

### 2. Improved Parameter Descriptions

#### Pattern Parameter
**Before:**
```
"Regex pattern to search for in entity names. Use this for broad or partial name searches."
```

**After:**
```
"Regex pattern to search for in entity names. IMPORTANT: D365 F&O entity names have specific conventions. For customer groups, try: 'Customer.*Group', 'Cust.*Group', '.*CustomerGroup.*', 'Commission.*Group', or just 'Group' to find all group entities. For broader searches, use '.*Customer.*' or '.*' (with limit). Case-sensitive regex matching."
```

### 3. Enhanced Response with Suggestions
Added intelligent suggestions when no results are found:

```json
{
  "entities": [],
  "totalCount": 0,
  "returnedCount": 0,
  "searchTime": 0.321,
  "pattern": ".*[Cc]ustomer.*[Gg]roup.*",
  "limit": 50,
  "filters": {...},
  "suggestions": [
    "Try broader patterns like '.*Customer.*', '.*Group.*', or '.*' (with small limit)",
    "Use category filters: entity_category='Master' for customer groups",
    "Check data_service_enabled=True for API-accessible entities",
    "Common D365 F&O patterns: 'Cust' for Customer, 'Vend' for Vendor, 'Ledger' for GL"
  ],
  "broaderMatches": [...],
  "ftsMatches": [...]
}
```

### 4. Intelligent Fallback Search
When the primary search returns no results, the tool now automatically attempts:
1. **Broader regex searches** based on extracted terms
2. **FTS5 full-text search** using SQLite FTS index
3. **Data entity info retrieval** for FTS results

### 5. **NEW: FTS5 Full-Text Search Integration**

#### Smart Term Extraction
The tool now extracts meaningful search terms from regex patterns:
- `.*[Cc]ustomer.*[Gg]roup.*` → `"Customer Group"`
- `Customer.*Group` → `"Customer Group"`
- `Commission.*Group` → `"Commission Group"`

#### FTS Search Process
When regex search returns no results:
1. Extract search terms from the regex pattern
2. Create a `SearchQuery` for FTS5 search
3. Execute full-text search using `MetadataSearchEngine`
4. Retrieve full `DataEntityInfo` for each FTS result
5. Include FTS results with relevance scores and snippets

#### FTS Response Enhancement
```json
{
  "ftsMatches": [
    {
      "name": "CustChargeCustomerGroupEntity",
      "public_entity_name": "CustomerChargeGroups",
      "public_collection_name": "CustomerChargeGroup",
      "label_text": "Customer charge groups",
      "fts_relevance": 0.87,
      "fts_snippet": "Customer ... groups ... charge"
    }
  ]
}
```

### 6. Technical Implementation

#### New Methods Added
```python
async def _try_fts_search(self, client, pattern: str) -> List[dict]:
    """Try FTS5 full-text search when regex search fails"""
    
def _extract_search_terms(self, pattern: str) -> str:
    """Extract meaningful search terms from regex pattern"""
```

#### FTS Integration Flow
1. **Regex Search** - Primary search using existing regex patterns
2. **Broader Search** - If no results, try broader regex patterns
3. **FTS Search** - If still no results, extract terms and use FTS5
4. **Entity Retrieval** - Get full entity details for FTS results
5. **Enhanced Response** - Include all search attempts in response

#### MetadataSearchEngine Usage
```python
from ...metadata_cache import MetadataSearchEngine
from ...models import SearchQuery

search_engine = MetadataSearchEngine(client.metadata_cache)
query = SearchQuery(
    text=search_text,
    entity_types=["data_entity"],
    limit=5,
    use_fulltext=True
)
fts_results = await search_engine.search(query)
```

## Expected Impact

### For AI Assistants
- Better understanding of D365 F&O naming conventions
- More specific and helpful search patterns
- Fallback strategies when initial searches fail
- Context-aware suggestions for refinement
- **Access to full-text search capabilities**

### For Users
- Faster discovery of relevant entities
- Better guidance when searches don't return expected results
- More intuitive search experience
- Reduced trial-and-error in finding entities
- **Intelligent full-text search when regex patterns fail**

## Common D365 F&O Entity Patterns

### Customer Entities
- `Customer.*` - General customer entities
- `Cust.*` - Abbreviated customer entities
- `.*Customer.*` - Entities containing "customer" anywhere

### Group Entities
- `.*Group.*` - Any entity with "group" in the name
- `.*CustomerGroup.*` - Customer group specific entities
- `Commission.*Group` - Commission-related group entities
- `CustCharge.*Group` - Customer charge group entities

### FTS Search Terms
- Use simple terms: `"customer group"`, `"commission"`, `"charge"`
- FTS handles: stemming, relevance scoring, snippet highlighting
- Supports: phrase queries, boolean operators, prefix matching

## Testing
All improvements maintain backward compatibility and have been tested for:
- Correct JSON schema validation
- Proper tool definition generation
- Error handling in fallback searches
- **FTS search integration**
- **Term extraction accuracy**
- Response format consistency

## Usage Examples

### Before Improvements
AI would generate patterns like:
```json
{"pattern": ".*[Cc]ustomer.*[Gg]roup.*"}
```
And get no results with no guidance.

### After Improvements
AI gets suggestions to try:
```json
{"pattern": ".*Customer.*"}
{"pattern": "Group"}
{"pattern": "Customer.*Group"}
```
Plus automatic broader matches and **FTS search results** when primary search fails.

## Files Modified
- `src/d365fo_client/mcp/tools/metadata_tools.py` - Enhanced tool definitions, FTS integration, and response logic
- `docs/MCP_SEARCH_IMPROVEMENTS.md` - This documentation

## Future Enhancements
1. **Pattern Templates** - Predefined search templates for common entity types
2. **Fuzzy Matching** - Support for approximate string matching
3. **Category-based Suggestions** - Suggest searches based on entity categories
4. **Search History** - Learn from successful search patterns
5. **Label-based Search** - Search by human-readable labels in addition to entity names
6. **Enhanced FTS** - Support for more complex FTS queries and operators
7. **Semantic Search** - AI-powered semantic understanding of search intent