# D365 Finance & Operations Service Discovery Specification

## Overview

This specification defines a comprehensive approach to discover, analyze, and document D365 Finance & Operations JSON and SOAP services, including their operations, parameters, data contracts, and schemas.

## Service Discovery Architecture

### 1. Service Group Discovery

**Endpoint Pattern**: `/api/services`
- **Purpose**: Discover all available service groups
- **Method**: GET
- **Authentication**: Bearer token (Azure AD)
- **Response Format**: JSON array of service groups

```json
{
  "ServiceGroups": [
    {"Name": "ServiceGroupName1"},
    {"Name": "ServiceGroupName2"}
  ]
}
```

### 2. Service Discovery within Groups

**Endpoint Pattern**: `/api/services/{ServiceGroupName}`
- **Purpose**: Discover services within a specific service group
- **Method**: GET
- **Response Format**: JSON array of services

```json
{
  "Services": [
    {"Name": "ServiceName1"},
    {"Name": "ServiceName2"}
  ]
}
```

### 3. Operation Discovery

**Endpoint Pattern**: `/api/services/{ServiceGroupName}/{ServiceName}`
- **Purpose**: Discover operations within a specific service
- **Method**: GET
- **Response Format**: JSON array of operations

```json
{
  "Operations": [
    {"Name": "OperationName1"},
    {"Name": "OperationName2"}
  ]
}
```

## Schema Discovery Architecture

### 1. WSDL Discovery

**Primary Endpoint**: `/soap/services/{ServiceGroupName}?wsdl`
- **Purpose**: Get main WSDL definition with operation signatures
- **Method**: GET
- **Authentication**: Bearer token (Azure AD)
- **Response Format**: XML WSDL

**Detailed Schema Endpoint**: `/soap/services/{ServiceGroupName}?wsdl=wsdl0`
- **Purpose**: Get detailed WSDL with parameter element definitions
- **Response Format**: XML WSDL with XSD imports

### 2. XSD Schema Discovery

**Schema Endpoint Pattern**: `/soap/services/{ServiceGroupName}?xsd=xsd{N}`
- **Purpose**: Get specific XSD schema definitions
- **Parameters**:
  - `xsd0`: Serialization schemas
  - `xsd1`: Array schemas
  - `xsd2`: Main operation schemas
  - `xsd3`: Application data contracts
  - `xsd4`: Xpp object base schemas
  - `xsd5`: Kernel interop schemas
  - `xsd6`: Dynamic data contracts

## Service Analysis Tools Specification

### Tool 1: Service Group Enumerator

**Purpose**: Discover and catalog all service groups in D365 F&O

**Function Signature**:
```typescript
async function discoverServiceGroups(): Promise<ServiceGroup[]>
```

**Implementation**:
1. Call `/api/services` endpoint
2. Parse JSON response
3. Extract service group names
4. Return structured list

**Output Schema**:
```typescript
interface ServiceGroup {
  name: string;
  discoveredAt: Date;
  services?: Service[];
}
```

### Tool 2: Service Enumerator

**Purpose**: Discover services within each service group

**Function Signature**:
```typescript
async function discoverServices(serviceGroupName: string): Promise<Service[]>
```

**Implementation**:
1. Call `/api/services/{serviceGroupName}` endpoint
2. Parse JSON response
3. Extract service names
4. Return structured list

**Output Schema**:
```typescript
interface Service {
  name: string;
  serviceGroup: string;
  operations?: Operation[];
}
```

### Tool 3: Operation Enumerator

**Purpose**: Discover operations within each service

**Function Signature**:
```typescript
async function discoverOperations(serviceGroupName: string, serviceName: string): Promise<Operation[]>
```

**Implementation**:
1. Call `/api/services/{serviceGroupName}/{serviceName}` endpoint
2. Parse JSON response
3. Extract operation names
4. Return structured list

**Output Schema**:
```typescript
interface Operation {
  name: string;
  service: string;
  serviceGroup: string;
  parameters?: Parameter[];
  returnType?: DataContract;
}
```

### Tool 4: WSDL Schema Analyzer

**Purpose**: Extract operation signatures and parameter definitions from WSDL

**Function Signature**:
```typescript
async function analyzeWSDL(serviceGroupName: string): Promise<WSDLAnalysis>
```

**Implementation**:
1. Call `/soap/services/{serviceGroupName}?wsdl=wsdl0`
2. Parse XML WSDL
3. Extract operation definitions
4. Identify XSD schema imports
5. Return structured analysis

**Output Schema**:
```typescript
interface WSDLAnalysis {
  serviceGroup: string;
  operations: OperationSignature[];
  schemaImports: SchemaImport[];
  messages: MessageDefinition[];
}

interface OperationSignature {
  name: string;
  inputMessage: string;
  outputMessage: string;
  faultMessage?: string;
  soapAction: string;
}

interface SchemaImport {
  namespace: string;
  schemaLocation: string;
  xsdNumber: number;
}
```

### Tool 5: XSD Schema Parser

**Purpose**: Parse XSD schemas to extract data contract definitions

**Function Signature**:
```typescript
async function parseXSDSchema(serviceGroupName: string, xsdNumber: number): Promise<DataContractSchema>
```

**Implementation**:
1. Call `/soap/services/{serviceGroupName}?xsd=xsd{xsdNumber}`
2. Parse XML XSD
3. Extract complex types, elements, and enumerations
4. Build data contract definitions
5. Return structured schema

**Output Schema**:
```typescript
interface DataContractSchema {
  namespace: string;
  targetNamespace: string;
  complexTypes: ComplexType[];
  elements: Element[];
  simpleTypes: SimpleType[];
}

interface ComplexType {
  name: string;
  extends?: string;
  properties: Property[];
  isAbstract?: boolean;
}

interface Property {
  name: string;
  type: string;
  minOccurs?: number;
  maxOccurs?: number;
  nillable?: boolean;
}

interface SimpleType {
  name: string;
  restriction: string;
  enumeration?: EnumValue[];
}

interface EnumValue {
  value: string;
  annotation?: string;
}
```

### Tool 6: Service Operation Tester

**Purpose**: Test service operations to understand parameter requirements

**Function Signature**:
```typescript
async function testOperation(
  serviceGroup: string, 
  service: string, 
  operation: string, 
  parameters: any
): Promise<OperationTestResult>
```

**Implementation**:
1. Call JSON service operation via MCP tools
2. Capture success/failure responses
3. Analyze error messages for parameter hints
4. Return test results with parameter discovery

**Output Schema**:
```typescript
interface OperationTestResult {
  success: boolean;
  statusCode: number;
  response?: any;
  errorMessage?: string;
  discoveredParameters?: string[];
  parameterHints?: ParameterHint[];
}

interface ParameterHint {
  parameterName: string;
  source: 'error_message' | 'schema' | 'inference';
  type?: string;
  required: boolean;
}
```

## Complete Service Documentation Generator

### Tool 7: Comprehensive Service Documenter

**Purpose**: Generate complete documentation for a service group

**Function Signature**:
```typescript
async function documentServiceGroup(serviceGroupName: string): Promise<ServiceGroupDocumentation>
```

**Implementation Flow**:
1. **Discovery Phase**:
   - Discover services in group
   - Discover operations in each service
   - Get WSDL analysis
   - Parse all XSD schemas

2. **Analysis Phase**:
   - Map operations to data contracts
   - Resolve parameter types
   - Identify inheritance relationships
   - Extract enumeration values

3. **Testing Phase**:
   - Test operations with empty parameters
   - Capture parameter requirement errors
   - Build parameter requirement matrix

4. **Documentation Phase**:
   - Generate markdown documentation
   - Create operation examples
   - Document data contracts
   - Provide usage patterns

**Output Schema**:
```typescript
interface ServiceGroupDocumentation {
  serviceGroup: string;
  discoveredAt: Date;
  services: ServiceDocumentation[];
  dataContracts: DataContract[];
  enumerations: EnumerationDocumentation[];
  examples: OperationExample[];
  usagePatterns: UsagePattern[];
}

interface ServiceDocumentation {
  name: string;
  operations: OperationDocumentation[];
  purpose?: string;
  businessContext?: string;
}

interface OperationDocumentation {
  name: string;
  purpose?: string;
  parameters: ParameterDocumentation[];
  returnType?: string;
  examples: OperationExample[];
  errorConditions: ErrorCondition[];
}

interface ParameterDocumentation {
  name: string;
  type: string;
  required: boolean;
  description?: string;
  validation?: ValidationRule[];
  examples: any[];
}
```

## Error Analysis and Parameter Discovery

### Error Message Patterns

Based on our exploration, common error patterns reveal parameter requirements:

1. **Missing Parameter Error**:
   ```
   "Parameter '{parameterName}' is not found within the request content body."
   ```
   - **Action**: Add parameter to required list
   - **Extract**: Parameter name from error message

2. **Abstract Class Error**:
   ```
   "Cannot create an abstract class."
   ```
   - **Action**: Investigate concrete implementations
   - **Requires**: Schema analysis to find concrete types

3. **Invalid Value Error**:
   ```
   "Data entity {entityName} does not exist."
   ```
   - **Action**: Validate against available entities
   - **Requires**: Cross-reference with entity discovery

4. **Business Logic Error**:
   ```
   "No entities were specified."
   ```
   - **Action**: Ensure required business objects are provided
   - **Requires**: Understanding of business context

## Implementation Strategy

### Phase 1: Core Discovery
- Implement service group, service, and operation discovery
- Build basic WSDL parsing capability
- Create operation testing framework

### Phase 2: Schema Analysis
- Implement XSD schema parsing
- Build data contract extraction
- Create type mapping and resolution

### Phase 3: Documentation Generation
- Implement comprehensive documentation generator
- Add examples and usage patterns
- Create validation and testing framework

### Phase 4: Integration and Automation
- Integrate with MCP D365FO tools
- Add automated discovery pipelines
- Create service change detection

## Tool Integration with MCP Server

The specification should integrate with existing MCP D365FO tools:

### Existing MCP Tools to Leverage
- `mcp_d365fo_call_json_service`: For operation testing
- `mcp_d365fo_search_entities`: For entity validation
- `mcp_d365fo_get_entity_schema`: For entity schema cross-reference

### New MCP Tools to Implement
- `mcp_d365fo_discover_service_groups`: Service group discovery
- `mcp_d365fo_discover_services`: Service discovery
- `mcp_d365fo_discover_operations`: Operation discovery
- `mcp_d365fo_analyze_wsdl`: WSDL analysis
- `mcp_d365fo_parse_xsd_schema`: XSD schema parsing
- `mcp_d365fo_document_service_group`: Complete documentation generation

## Usage Examples

### Complete Service Group Analysis
```typescript
// Discover and document a complete service group
const documentation = await documentServiceGroup("SystemNotificationServiceGroup");

// Output includes:
// - All services and operations
// - Complete data contracts with schemas
// - Parameter requirements and examples
// - Business context and usage patterns
```

### Parameter Discovery Workflow
```typescript
// Test operation to discover parameters
const testResult = await testOperation(
  "DMFServiceGroup", 
  "DataManagementTemplate", 
  "Export", 
  {}
);

// Analyze error messages for parameter hints
const parameters = extractParametersFromError(testResult.errorMessage);

// Get schema information for discovered parameters
const schema = await parseXSDSchema("DMFServiceGroup", 2);
const parameterTypes = resolveParameterTypes(parameters, schema);
```

This specification provides a comprehensive framework for discovering, analyzing, and documenting D365 F&O services, enabling automated generation of complete service documentation with schemas, parameters, and usage examples.