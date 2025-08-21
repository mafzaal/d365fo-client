#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Search for data entities in D365 Finance & Operations

.DESCRIPTION
    This script searches for data entities using the d365fo-client CLI.
    It supports pattern-based searching and various output formats.

.PARAMETER Pattern
    Search pattern for entity names (supports regex)

.PARAMETER Output
    Output format: json, table, csv, yaml (default: table)

.PARAMETER Limit
    Maximum number of results to return

.PARAMETER BaseUrl
    D365 F&O environment URL (optional if configured in profile)

.PARAMETER Profile
    Configuration profile to use

.PARAMETER VerboseOutput
    Enable verbose output

.EXAMPLE
    .\search_data_entities.ps1 -Pattern "customer"
    
.EXAMPLE
    .\search_data_entities.ps1 -Pattern ".*sales.*" -Output json -Limit 10

.EXAMPLE
    .\search_data_entities.ps1 -Pattern "inventory" -Profile prod -VerboseOutput
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Pattern,
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("json", "table", "csv", "yaml")]
    [string]$Output = "table",
    
    [Parameter(Mandatory=$false)]
    [int]$Limit,
    
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

$cmdArgs += @("metadata", "search", $Pattern, "--type", "entities")

if ($Limit) { $cmdArgs += @("--limit", $Limit) }

Write-Host "Searching for data entities with pattern: $Pattern" -ForegroundColor Green

try {
    # Execute the d365fo-client command
    uv run d365fo-client @cmdArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`nSearch completed successfully!" -ForegroundColor Green
    } else {
        Write-Host "`nSearch failed with exit code: $LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }
} catch {
    Write-Host "Error executing search: $_" -ForegroundColor Red
    exit 1
}