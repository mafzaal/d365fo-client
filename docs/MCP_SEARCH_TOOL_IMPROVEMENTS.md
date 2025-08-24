# MCP Search Tool Description Improvements

## Problem Statement

The AI assistants were confused when using the MCP search tools, often:
- Using example patterns as literal search terms instead of building appropriate patterns
- Performing single searches instead of breaking down requests into keywords
- Missing relevant results due to overly specific or inappropriate search patterns

## Solution

Updated the descriptions for all three major search tools to guide AI assistants to:
1. **Break down requests into individual keywords**
2. **Perform multiple searches for each keyword** 
3. **Analyze and combine results from all searches**
4. **Build appropriate regex patterns instead of using examples literally**

## Updated Tools

### 1. d365fo_search_entities

**Previous Behavior**: When asked "Get data management entities", AI would search for exact patterns like "Customer.*Group" 

**New Behavior**: AI will:
1. Extract keywords: "data", "management", "entities"
2. Create patterns: ".*[Dd]ata.*", ".*[Mm]anagement.*"
3. Perform separate searches for each keyword
4. Analyze combined results to find entities matching both concepts

### 2. d365fo_search_actions

**Previous Behavior**: Generic searches with vague patterns

**New Behavior**: For "posting actions":
1. Extract keywords: "post", "posting"
2. Create pattern: ".*[Pp]ost.*"
3. Search for related terms and variations
4. Combine results to find posting-related actions

### 3. d365fo_search_enumerations

**Previous Behavior**: Using example patterns literally

**New Behavior**: For "customer status enums":
1. Extract keywords: "customer", "status"
2. Create patterns: ".*[Cc]ustomer.*", ".*[Ss]tatus.*"
3. Perform multiple searches
4. Find enums that match both concepts

## Key Improvements

### 1. Keyword Extraction Strategy
```
Request: "Get data management entities"
Keywords: ["data", "management", "entities"]
Patterns: [".*[Dd]ata.*", ".*[Mm]anagement.*"]
Actions: Perform 2 separate searches, analyze overlap
```

### 2. Pattern Building Guidelines
- Use case-insensitive patterns: `[Cc]ustomer` instead of `customer`
- Add word boundaries: `.*[Kk]eyword.*`
- Don't use examples literally: Build patterns from actual request keywords
- Multiple searches: One pattern per significant keyword

### 3. Multi-Search Analysis
- Perform separate searches for each keyword
- Look for entities/actions/enums appearing in multiple result sets
- Prioritize results that match multiple keywords
- Provide comprehensive coverage of the search space

## Example Usage Scenarios

### Scenario 1: "Find customer group entities"
**Old Approach**: Single search with "Customer.*Group"
**New Approach**:
1. Search for ".*[Cc]ustomer.*" → Get all customer-related entities
2. Search for ".*[Gg]roup.*" → Get all group-related entities  
3. Analyze intersection to find customer group entities
4. Review both result sets for comprehensive coverage

### Scenario 2: "Get posting actions"
**Old Approach**: Single search with vague pattern
**New Approach**:
1. Search for ".*[Pp]ost.*" → Get posting-related actions
2. Search for ".*[Jj]ournal.*" → Get journal-related actions (related concept)
3. Combine results to find all posting/journaling actions
4. Analyze action names and descriptions for relevance

### Scenario 3: "Find approval workflow enums"
**Old Approach**: Use example pattern literally
**New Approach**:
1. Search for ".*[Aa]pprov.*" → Get approval-related enums
2. Search for ".*[Ww]orkflow.*" → Get workflow-related enums
3. Search for ".*[Ss]tatus.*" → Get status-related enums (often used in workflows)
4. Analyze overlap and review enum members for workflow approval concepts

## Technical Implementation

### Updated Description Structure
Each search tool now includes:
- **Strategy explanation**: How to break down requests
- **Multiple search guidance**: Perform separate searches per keyword
- **Pattern building rules**: Create regex from keywords, not examples
- **Analysis instructions**: Combine and evaluate results

### Pattern Construction Guidelines
```python
# Good pattern building:
Request: "customer groups"
Keywords: ["customer", "groups"]
Patterns: [".*[Cc]ustomer.*", ".*[Gg]roup.*"]

# Bad pattern usage:
Using literal examples: "Customer.*Group" 
```

### Search Strategy Template
```
1. EXTRACT: Identify keywords from user request
2. BUILD: Create regex patterns for each keyword  
3. SEARCH: Perform separate search for each pattern
4. ANALYZE: Combine results and find intersections
5. REPORT: Present comprehensive findings
```

## Benefits

1. **Better Coverage**: Multiple searches ensure comprehensive results
2. **Accurate Targeting**: Keyword-based patterns match user intent
3. **Reduced Confusion**: Clear instructions prevent misuse of examples
4. **Improved Relevance**: Multi-keyword analysis finds more precise matches
5. **Consistent Behavior**: Standardized approach across all search tools

## Testing Recommendations

When testing the improved search tools:

1. **Test keyword extraction**: Verify AI breaks down "data management entities" correctly
2. **Test multiple searches**: Confirm AI performs separate searches per keyword
3. **Test pattern building**: Ensure AI creates regex patterns, not literal examples
4. **Test result analysis**: Verify AI combines and analyzes multiple search results
5. **Test edge cases**: Complex requests with 3+ keywords, technical terms, etc.

## Future Enhancements

1. **Synonym Support**: Add guidance for searching related terms (e.g., "customer" → "cust", "client")
2. **Domain Knowledge**: Include D365 F&O-specific keyword mappings
3. **Result Ranking**: Guidance for prioritizing results based on keyword matches
4. **Performance Optimization**: Strategies for limiting searches when needed