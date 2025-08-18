#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Get detailed schema information for a data entity in D365 Finance & Operations

.DESCRIPTION
    This script retrieves detailed schema information for a specific data entity 
    using the d365fo-client CLI, including properties, keys, and labels.

.PARAMETER EntityName
    Name of the entity to get schema information for

.PARAMETER Output
    Output format: json, table, csv, yaml (default: table)

.PARAMETER Properties
    Include detailed property information

.PARAMETER Keys
    Include key field information

.PARAMETER Labels
    Include label information

.PARAMETER BaseUrl
    D365 F&O environment URL (optional if configured in profile)

.PARAMETER Profile
    Configuration profile to use

.PARAMETER VerboseOutput
    Enable verbose output

.EXAMPLE
    .\get_data_entity_schema.ps1 -EntityName "CustomersV3"
    
.EXAMPLE
    .\get_data_entity_schema.ps1 -EntityName "SalesOrderHeaders" -Properties -Keys -Labels -Output json

.EXAMPLE
    .\get_data_entity_schema.ps1 -EntityName "Items" -Profile prod -VerboseOutput
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$EntityName,
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("json", "table", "csv", "yaml")]
    [string]$Output = "table",
    
    [Parameter(Mandatory=$false)]
    [switch]$Properties,
    
    [Parameter(Mandatory=$false)]
    [switch]$Keys,
    
    [Parameter(Mandatory=$false)]
    [switch]$Labels,
    
    [Parameter(Mandatory=$false)]
    [string]$BaseUrl,
    
    [Parameter(Mandatory=$false)]
    [string]$Profile,
    
    [Parameter(Mandatory=$false)]
    [switch]$VerboseOutput
)

# Build command arguments
$cmdArgs = @()

if ($Output) { $cmdArgs += @("--output", $Output) }
if ($BaseUrl) { $cmdArgs += @("--base-url", $BaseUrl) }
if ($Profile) { $cmdArgs += @("--profile", $Profile) }
if ($VerboseOutput) { $cmdArgs += "--verbose" }

$cmdArgs += @("metadata", "info", $EntityName)

if ($Properties) { $cmdArgs += "--properties" }
if ($Keys) { $cmdArgs += "--keys" }
if ($Labels) { $cmdArgs += "--labels" }

Write-Host "Getting schema information for entity: $EntityName" -ForegroundColor Green

try {
    # Execute the d365fo-client command
    uv run d365fo-client @cmdArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`nSchema retrieval completed successfully!" -ForegroundColor Green
    } else {
        Write-Host "`nSchema retrieval failed with exit code: $LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }
} catch {
    Write-Host "Error executing schema retrieval: $_" -ForegroundColor Red
    exit 1
}