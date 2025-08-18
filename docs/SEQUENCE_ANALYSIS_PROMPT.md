# Sequence Number Analysis Prompt

## Overview

The Sequence Number Analysis prompt is a comprehensive MCP (Model Context Protocol) prompt designed to analyze Microsoft Dynamics 365 Finance & Operations sequence numbers. This prompt enables AI assistants to perform deep analysis of sequence number configurations, usage patterns, and health metrics.

## Features

### Analysis Types

1. **Manual Sequences** (`manual_sequences`)
   - Identifies all manually configured sequence numbers
   - Analyzes manual override patterns and risks
   - Reviews access controls and permissions

2. **Entity References** (`entity_references`)
   - Maps which entities use which sequence numbers
   - Identifies orphaned or unused sequences
   - Validates reference consistency across scopes

3. **Configuration Review** (`configuration_review`)
   - Validates sequence configuration consistency
   - Checks scope alignment between tables
   - Reviews format and interval settings

4. **Usage Patterns** (`usage_patterns`)
   - Analyzes sequence utilization rates
   - Identifies sequences approaching limits
   - Reviews performance and preallocation settings

5. **Comprehensive** (`comprehensive`)
   - Combines all analysis types
   - Provides complete sequence health assessment
   - Generates actionable recommendations

### Scope Options

- **Company** - Analyze sequences for specific companies
- **Legal Entity** - Focus on legal entity scoped sequences
- **Operating Unit** - Analyze operating unit sequences
- **Global** - Review globally scoped sequences
- **All** - Analyze across all scopes

## Data Sources

The prompt automatically retrieves data from the following D365FO entities:

### Primary Entities
- `SequenceV2Tables` - Main sequence configuration
- `NumberSequencesV2References` - Entity-to-sequence mappings
- `NumberSequenceScope` - Scope definitions
- `NumberSequenceGroup` - Sequence groupings
- `NumberSequenceTable` - Legacy sequence table

### Parameter Tables
- `CustParameters` - Customer parameters
- `VendParameters` - Vendor parameters  
- `InventParameters` - Inventory parameters
- `SalesParameters` - Sales parameters
- `ProjParameters` - Project parameters

## Key Analysis Areas

### 1. Configuration Analysis
- **Sequence Identification**: Code, name, company assignment
- **Scope Configuration**: Type, value, operating unit restrictions
- **Value Management**: Current value, limits, format specifications
- **Behavior Settings**: Manual/automatic, continuous, cyclical options
- **Status Information**: Active/stopped status, cleanup settings

### 2. Usage Pattern Analysis
- **Entity Mapping**: Which business entities use each sequence
- **Volume Analysis**: Utilization rates and capacity planning
- **Performance Impact**: Preallocation effectiveness
- **Gap Analysis**: Missing numbers in continuous sequences

### 3. Health Assessment
- **Consistency Validation**: Cross-table validation
- **Performance Metrics**: Response times and bottlenecks
- **Risk Identification**: Sequences approaching limits
- **Security Review**: Access controls and permissions

### 4. Business Impact Analysis
- **Process Dependencies**: Critical business process mapping
- **Risk Assessment**: Impact of sequence failures
- **Cross-Company Alignment**: Multi-entity consistency
- **Upgrade Readiness**: Version compatibility

## Output Format

The analysis provides structured output including:

1. **Executive Summary**
   - Key findings and critical issues
   - Health score and risk indicators
   - Immediate action items

2. **Detailed Entity Analysis**
   - Per-sequence configuration breakdown
   - Usage statistics and patterns
   - Performance metrics

3. **Cross-Reference Mapping**
   - Entity-to-sequence relationships
   - Reference validation results
   - Orphaned or unused sequences

4. **Health Assessment**
   - Configuration consistency check
   - Performance evaluation
   - Capacity planning metrics

5. **Risk Analysis**
   - Potential failure points
   - Business impact assessment
   - Mitigation strategies

6. **Action Plan**
   - Prioritized recommendations
   - Implementation guidance
   - Monitoring strategies

## Usage Examples

### Basic Usage

```python
from d365fo_client.mcp.prompts.sequence_analysis import (
    SequenceAnalysisPromptArgs,
    SequenceAnalysisType,
    SequenceScope
)

# Analyze all manual sequences
args = SequenceAnalysisPromptArgs(
    analysis_type=SequenceAnalysisType.MANUAL_SEQUENCES,
    scope=SequenceScope.ALL,
    include_recommendations=True
)
```

### Specific Company Analysis

```python
# Analyze sequences for specific companies
args = SequenceAnalysisPromptArgs(
    analysis_type=SequenceAnalysisType.COMPREHENSIVE,
    scope=SequenceScope.COMPANY,
    company_codes=["USMF", "USRT"],
    include_usage_stats=True
)
```

### Entity-Specific Analysis

```python
# Analyze customer-related sequences
args = SequenceAnalysisPromptArgs(
    analysis_type=SequenceAnalysisType.ENTITY_REFERENCES,
    entity_filter="Cust",
    include_metadata=True
)
```

## OData Queries

The prompt includes predefined OData queries for data retrieval:

### All Sequences
```odata
SequenceV2Tables?$select=NumberSequenceCode,ScopeType,ScopeValue,Name,NextRec,Format,
Preallocation,Manual,LowestValue,HighestValue,Company,Interval,AnnotatedFormat,
SmallestValue,LargestValue,CleanupTimeToLive,DateAndTime,Qty,Cyclical,Continuous,
Stopped,InUse,SkipCounting,OperatingUnitType&$orderby=Company,NumberSequenceCode
```

### Manual Sequences Only
```odata
SequenceV2Tables?$filter=Manual eq true&$select=NumberSequenceCode,ScopeType,
ScopeValue,Name,NextRec,Format,Company,InUse,Stopped&$orderby=Company,NumberSequenceCode
```

### Sequence References
```odata
NumberSequencesV2References?$select=DataTypeName,NumberSequenceCode,ReuseNumbers,
ScopeType,ScopeValue,Company,AllowUserChanges,Continuous&$orderby=NumberSequenceCode,DataTypeName
```

### Near Limit Sequences
```odata
SequenceV2Tables?$filter=LargestValue gt 0 and NextRec gt 0&$select=NumberSequenceCode,
Name,Company,NextRec,LargestValue,Format&$orderby=Company,NumberSequenceCode
```

## Risk Indicators

The analysis identifies several risk indicators:

- **Capacity Risks**: NextRec approaching LargestValue
- **Configuration Risks**: Stopped sequences still referenced
- **Security Risks**: Manual sequences without proper controls
- **Consistency Risks**: Inconsistent scope configurations
- **Integration Risks**: Missing references for active entities
- **Performance Risks**: Preallocation disabled on high-volume sequences

## Recommendations

The prompt generates actionable recommendations in several categories:

### Configuration Optimization
- Format improvements for better readability
- Preallocation tuning for performance
- Interval adjustments for efficiency

### Security Hardening
- Access control improvements
- Manual override policy enforcement
- Audit trail implementation

### Performance Enhancement
- Cleanup strategy optimization
- Capacity planning improvements
- Monitoring implementation

### Maintenance Planning
- Regular health check schedules
- Capacity monitoring alerts
- Cleanup automation

## Integration with MCP Server

The sequence analysis prompt is designed for seamless integration with MCP servers:

```python
# MCP Server registration
SEQUENCE_ANALYSIS_PROMPT = {
    "name": "d365fo_sequence_analysis",
    "description": "Comprehensive analysis of D365 Finance & Operations sequence numbers",
    "arguments": SequenceAnalysisPromptArgs,
    "template": SequenceAnalysisPrompt.get_prompt_template(),
    "data_queries": SequenceAnalysisPrompt.get_data_retrieval_queries(),
    "metadata": SequenceAnalysisPrompt.get_analysis_metadata()
}
```

## Best Practices

1. **Regular Health Checks**: Schedule monthly sequence health assessments
2. **Capacity Planning**: Monitor sequences approaching 80% capacity
3. **Security Reviews**: Quarterly review of manual sequence permissions
4. **Performance Monitoring**: Track sequence allocation performance
5. **Documentation**: Maintain sequence documentation and ownership
6. **Testing**: Validate sequence behavior in test environments
7. **Cleanup**: Regular cleanup of unused or obsolete sequences

## Common Use Cases

### Operations Team
- Monitor sequence health and capacity
- Identify and resolve numbering issues
- Plan for sequence maintenance windows

### Development Team
- Analyze sequence usage for new implementations
- Validate sequence configuration consistency
- Plan for system upgrades and migrations

### Security Team
- Review access controls and permissions
- Audit manual sequence usage
- Implement security policies

### Business Analysts
- Understand sequence usage patterns
- Assess business impact of sequence changes
- Plan for business process improvements

## Troubleshooting

### Common Issues

1. **Sequences Approaching Limits**
   - Increase LargestValue or implement cleanup
   - Enable preallocation for better performance
   - Consider format changes for larger ranges

2. **Performance Issues**
   - Enable preallocation
   - Adjust interval settings
   - Review cleanup configurations

3. **Consistency Problems**
   - Validate scope configurations
   - Check reference integrity
   - Review cross-company settings

4. **Security Concerns**
   - Review manual sequence permissions
   - Implement audit controls
   - Restrict user change allowances

## Related Documentation

- [D365FO Number Sequences Documentation](https://docs.microsoft.com/dynamics365/fin-ops-core/fin-ops/organization-administration/number-sequence-overview)
- [MCP Server Specification](../MCP_SERVER_SPECIFICATION.md)
- [D365FO Client Documentation](../../README.md)
- [Integration Testing Guide](../INTEGRATION_TESTING_IMPLEMENTATION.md)