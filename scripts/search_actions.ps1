#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Search for actions in D365 Finance & Operations

.DESCRIPTION
    This script searches for actions using the d365fo-client CLI.
    It supports pattern-based searching and filtering by entity.

.PARAMETER Pattern
    Search pattern for action names (optional)

.PARAMETER Entity
    Filter actions for a specific entity (optional)

.PARAMETER Output
    Output format: json, table, csv, yaml (default: table)

.PARAMETER BaseUrl
    D365 F&O environment URL (optional if configured in profile)

.PARAMETER Profile
    Configuration profile to use

.PARAMETER VerboseOutput
    Enable verbose output

.EXAMPLE
    .\search_actions.ps1
    
.EXAMPLE
    .\search_actions.ps1 -Pattern "post" -Output json

.EXAMPLE
    .\search_actions.ps1 -Entity "CustomersV3" -Profile prod -VerboseOutput
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$Pattern = "",
    
    [Parameter(Mandatory=$false)]
    [string]$Entity,
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("json", "table", "csv", "yaml")]
    [string]$Output = "table",
    
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

$cmdArgs += @("action", "list")

if ($Pattern) { $cmdArgs += $Pattern }
if ($Entity) { $cmdArgs += @("--entity", $Entity) }

if ($Pattern) {
    Write-Host "Searching for actions with pattern: $Pattern" -ForegroundColor Green
} else {
    Write-Host "Listing all available actions" -ForegroundColor Green
}

if ($Entity) {
    Write-Host "Filtering for entity: $Entity" -ForegroundColor Cyan
}

try {
    # Execute the d365fo-client command
    uv run d365fo-client @cmdArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`nAction search completed successfully!" -ForegroundColor Green
    } else {
        Write-Host "`nAction search failed with exit code: $LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }
} catch {
    Write-Host "Error executing action search: $_" -ForegroundColor Red
    exit 1
}