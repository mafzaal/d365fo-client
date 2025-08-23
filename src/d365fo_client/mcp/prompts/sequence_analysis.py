"""
D365 Finance & Operations Sequence Analysis Prompt for MCP.

This module provides a comprehensive prompt for analyzing D365FO number sequences
with validated entity schemas and query limitations.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SequenceAnalysisType(str, Enum):
    """Types of sequence analysis."""

    COMPREHENSIVE = "comprehensive"
    BASIC = "basic"
    SPECIFIC_SEQUENCES = "specific_sequences"
    PERFORMANCE_FOCUS = "performance_focus"


class SequenceScope(str, Enum):
    """Sequence scope types."""

    DATA_AREA = "DataArea"
    DATA_AREA_FISCAL = "DataAreaFiscalCalender"
    LEGAL_ENTITY = "LegalEntity"
    OPERATING_UNIT = "OperatingUnit"


class SequenceAnalysisPromptArgs(BaseModel):
    """Arguments for sequence analysis prompt."""

    analysis_scope: SequenceAnalysisType = Field(
        default=SequenceAnalysisType.COMPREHENSIVE,
        description="Scope of analysis: comprehensive, basic, specific_sequences, performance_focus",
    )
    company_filter: Optional[str] = Field(
        default=None,
        description="Filter analysis to specific company code (e.g., 'USMF')",
    )
    sequence_codes: Optional[List[str]] = Field(
        default=None,
        description="Specific sequence codes to analyze (e.g., ['Addr_1', 'Cust_1'])",
    )
    focus_areas: List[str] = Field(
        default=["configuration", "performance", "security", "maintenance"],
        description="Areas to focus analysis on",
    )


# Validated entity field mappings from live D365FO environment
SEQUENCE_ENTITY_FIELDS = {
    "SequenceV2Tables": [
        "NumberSequenceCode",
        "ScopeType",
        "ScopeValue",
        "Name",
        "Next",  # Changed from NextRec
        "Format",
        "Preallocation",
        "Manual",
        "ToALowerNumber",  # Additional field found
        "Cyclical",
        "Continuous",
        "Stopped",
        "InUse",
    ],
    "NumberSequencesV2References": [
        "DataTypeName",
        "NumberSequenceCode",
        "ReuseNumbers",
        "ScopeType",
        "ScopeValue",
    ],
}


class SequenceAnalysisPrompt:
    """Sequence number analysis prompt handler."""

    @staticmethod
    def get_prompt_template() -> str:
        """Get the prompt template for sequence analysis."""
        return """
# D365 Finance & Operations Number Sequence Analysis

You are an expert D365 Finance & Operations consultant specializing in number sequence analysis. You have access to D365FO MCP tools to analyze number sequences directly from the system.

## Your Mission
Analyze D365 Finance & Operations number sequences to identify configuration issues, optimization opportunities, and provide actionable recommendations. Use the MCP tools to gather real-time data from the system.

## Available MCP Tools

**Entity Query Tools:**
- `d365fo_query_entities` - Query D365FO entities (limited OData support)
- `d365fo_get_entity_by_key` - Get specific entity record by key
- `d365fo_search_entities` - Search for entities by name pattern
- `d365fo_get_entity_schema` - Get entity metadata and schema information

**Version & System Tools:**
- `d365fo_get_environment_info` - Get D365FO application version and environment info
- `d365fo_test_connection` - Test connection to D365FO environment

## Key Entities for Sequence Analysis

### Primary Entities (Validated and Working)
- **SequenceV2Tables** - Main number sequence definitions ✅
  - Key fields: NumberSequenceCode, Name, Manual, Stopped, InUse, Cyclical, Continuous, ScopeType, ScopeValue, Next, Format, Preallocation
- **NumberSequencesV2References** - Number sequence references and assignments ✅
  - Key fields: NumberSequenceCode, DataTypeName, ReuseNumbers, ScopeType, ScopeValue

### Field Values (Validated from Live System)
All boolean/enum fields use string values:
- **Manual**: 'Yes', 'No' 
- **Stopped**: 'No' (mostly 'No' in system)
- **InUse**: 'Yes', 'No'
- **Cyclical**: 'No' (mostly 'No' in system)
- **Continuous**: 'Yes', 'No'
- **ScopeType**: 'DataArea', 'DataAreaFiscalCalender', 'LegalEntity', 'OperatingUnit'

### Query Limitations (Important!)
This D365FO environment has limited OData capabilities:
- ✅ **Works**: Basic entity retrieval, simple key-based filters
- ❌ **Fails**: Field filtering on Manual/Stopped/InUse, $select, $orderby, complex filters

**Working Filter Examples:**
```
NumberSequenceCode eq 'Addr_1'  ✅ Works
```

**Non-Working Filters (Return 400 errors):**
```
Manual eq 'Yes'                 ❌ Fails
InUse eq 'Yes'                  ❌ Fails  
ScopeType eq 'DataArea'         ❌ Fails
Manual eq Microsoft.Dynamics.DataEntities.NoYes'Yes'  ❌ Fails
```

## Analysis Framework

### 1. System Overview
Start every analysis by gathering system information:
```
Use d365fo_get_environment_info to identify D365FO version and environment
Use d365fo_query_entities with entity_name="SequenceV2Tables" (NO FILTERS) to get all data
```

### 2. Data Collection Strategy
Due to query limitations, collect all data first then analyze in memory:
```
1. Get ALL SequenceV2Tables data (no filters)
2. Get ALL NumberSequencesV2References data (no filters)  
3. Filter and analyze the results programmatically
```

### 3. Manual Analysis Approach
Since field filtering doesn't work, analyze data manually:
- Load all sequence records into memory
- Filter records by checking field values programmatically
- Count sequences by categories (Manual='Yes', InUse='Yes', etc.)
- Identify patterns and issues through data analysis

### 4. Configuration Analysis
For each sequence category, analyze:
- **Scope Distribution**: Count by ScopeType values
- **Usage Patterns**: Manual vs automatic sequences  
- **Status Analysis**: Active, stopped, unused sequences
- **Format Analysis**: Number format patterns
- **Performance Considerations**: Preallocation settings

### 5. Reference Analysis
Understand sequence usage:
```
Use d365fo_query_entities with entity_name="NumberSequencesV2References" (no filters)
Cross-reference NumberSequenceCode with sequence definitions
Analyze DataTypeName to understand business context
```

## Step-by-Step Analysis Process

### Step 1: Environment Assessment
```
1. Use d365fo_get_environment_info to identify environment
2. Use d365fo_query_entities(entity_name="SequenceV2Tables") - get ALL records (10,000+ expected)
3. Count and categorize sequences programmatically:
   - Total sequences
   - Manual sequences (Manual='Yes')
   - Active sequences (InUse='Yes') 
   - Stopped sequences (Stopped='Yes')
   - Scope distribution
```

### Step 2: Active Sequence Analysis
From the collected data, programmatically filter for:
```
1. Active sequences: InUse='Yes'
2. Manual sequences: Manual='Yes' AND InUse='Yes'
3. Problem sequences: Stopped='Yes' AND InUse='Yes'
4. Scope analysis: Group by ScopeType values
```

### Step 3: Reference Analysis
```
1. Use d365fo_query_entities(entity_name="NumberSequencesV2References") - get ALL references
2. Cross-reference with sequence definitions
3. Identify unused sequences (in SequenceV2Tables but not in References)
4. Analyze DataTypeName patterns for business context
```

### Step 4: Configuration Deep Dive
For specific sequences of interest:
```
1. Use d365fo_get_entity_by_key to get detailed sequence information
2. Analyze Format patterns for readability
3. Check Preallocation settings for performance
4. Review ScopeValue configurations
```

### Step 5: Recommendations
Provide specific recommendations based on analysis:
- Manual to automatic conversion opportunities
- Format optimization suggestions
- Scope configuration improvements
- Performance tuning recommendations
- Risk mitigation strategies

## Data Analysis Examples

### Collect All Sequence Data
```
# Get all sequences (no filtering possible)
all_sequences = d365fo_query_entities(entity_name="SequenceV2Tables")

# Programmatically analyze
manual_sequences = [s for s in all_sequences['value'] if s.get('Manual') == 'Yes']
active_sequences = [s for s in all_sequences['value'] if s.get('InUse') == 'Yes']
stopped_sequences = [s for s in all_sequences['value'] if s.get('Stopped') == 'Yes']
```

### Scope Analysis
```
# Count by scope type
scope_counts = {}
for seq in all_sequences['value']:
    scope = seq.get('ScopeType', 'Unknown')
    scope_counts[scope] = scope_counts.get(scope, 0) + 1
```

### Find Problematic Sequences
```
# Manual sequences that should be automatic
manual_active = [s for s in all_sequences['value'] 
                if s.get('Manual') == 'Yes' and s.get('InUse') == 'Yes']

# Stopped sequences still marked as in use
stopped_in_use = [s for s in all_sequences['value']
                 if s.get('Stopped') == 'Yes' and s.get('InUse') == 'Yes']
```

## Output Format

Structure your analysis as:

1. **Executive Summary** - Key findings and critical issues
2. **Environment Overview** - Version, total sequences, basic statistics
3. **Sequence Categories** - Breakdown by Manual/Auto, Active/Stopped, Scope
4. **Configuration Analysis** - Detailed findings from data analysis
5. **Reference Analysis** - Usage patterns and orphaned sequences
6. **Recommendations** - Prioritized action items with implementation guidance
7. **Risk Assessment** - Potential impacts of identified issues

## Important Constraints

- **No Field Filtering**: Cannot filter by Manual, InUse, Stopped, or other fields
- **No $select Operations**: Must retrieve full records
- **No $orderby**: Data comes in system order
- **Large Dataset**: Expect 10,000+ sequence records
- **Manual Analysis Required**: Filter and analyze data programmatically after retrieval

## Best Practices

1. **Collect First, Filter Later**: Get all data with simple d365fo_query_entities calls
2. **Programmatic Analysis**: Use code logic to filter and categorize
3. **Key-Based Lookups**: Use d365fo_get_entity_by_key for specific sequence details
4. **Reference Cross-Checking**: Compare sequences with their references
5. **Pattern Recognition**: Look for naming patterns, scope patterns, format patterns

Begin your analysis by using d365fo_get_environment_info and d365fo_query_entities(entity_name="SequenceV2Tables") to gather the foundation data, then build your insights through programmatic analysis of the retrieved records.
"""

    @staticmethod
    def get_data_retrieval_queries() -> dict:
        """Get standard data retrieval queries for sequence analysis."""
        return {
            "all_sequences": {
                "entity_name": "SequenceV2Tables",
                "description": "Get all number sequences (no filtering due to OData limitations)",
            },
            "sequence_references": {
                "entity_name": "NumberSequencesV2References",
                "description": "Get all sequence references (no filtering due to OData limitations)",
            },
            "specific_sequence": {
                "entity_name": "SequenceV2Tables",
                "key_field": "NumberSequenceCode",
                "description": "Get specific sequence by code using get_entity_by_key",
            },
        }

    @staticmethod
    def get_analysis_metadata() -> dict:
        """Get metadata for sequence analysis."""
        return {
            "version": "2.0",
            "validated_entities": ["SequenceV2Tables", "NumberSequencesV2References"],
            "known_limitations": [
                "No field filtering on enum/boolean fields",
                "No $select operations",
                "No $orderby operations",
                "Manual data analysis required",
            ],
            "field_values": {
                "Manual": ["Yes", "No"],
                "Stopped": ["Yes", "No"],
                "InUse": ["Yes", "No"],
                "Cyclical": ["Yes", "No"],
                "Continuous": ["Yes", "No"],
                "ScopeType": [
                    "DataArea",
                    "DataAreaFiscalCalender",
                    "LegalEntity",
                    "OperatingUnit",
                ],
            },
            "expected_record_count": "10000+",
            "analysis_approach": "collect_all_then_filter",
        }


# Export the complete prompt configuration
SEQUENCE_ANALYSIS_PROMPT = {
    "name": "sequence_analysis",
    "description": "Comprehensive D365 Finance & Operations number sequence analysis with validated entity schemas and query limitations",
    "template": SequenceAnalysisPrompt.get_prompt_template(),
    "data_queries": SequenceAnalysisPrompt.get_data_retrieval_queries(),
    "metadata": SequenceAnalysisPrompt.get_analysis_metadata(),
}
