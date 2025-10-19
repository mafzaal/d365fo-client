#!/bin/bash
set -e

# Azure Container Apps Deployment Script for d365fo-client MCP Server
# This script deploys the d365fo-client Docker image to Azure Container Apps

# Configuration
RESOURCE_GROUP="${RESOURCE_GROUP:-d365fo-mcp-rg}"
LOCATION="${LOCATION:-eastus}"
CONTAINER_APP_ENV="${CONTAINER_APP_ENV:-d365fo-mcp-env}"
CONTAINER_APP_NAME="${CONTAINER_APP_NAME:-d365fo-mcp-server}"
IMAGE="ghcr.io/mafzaal/d365fo-client:latest"

# MCP Server Configuration (defaults for Azure Container Apps)
D365FO_MCP_TRANSPORT="${D365FO_MCP_TRANSPORT:-http}"
D365FO_MCP_HTTP_HOST="${D365FO_MCP_HTTP_HOST:-0.0.0.0}"
D365FO_MCP_HTTP_PORT="${D365FO_MCP_HTTP_PORT:-8000}"

# MCP Authentication Configuration (REQUIRED for internet-exposed endpoints)
# Choose one authentication method:
#
# Option 1: OAuth Authentication (recommended)
#   D365FO_MCP_AUTH_CLIENT_ID - Azure AD App Registration Client ID
#   D365FO_MCP_AUTH_CLIENT_SECRET - Azure AD App Registration Client Secret
#   D365FO_MCP_AUTH_TENANT_ID - Azure AD Tenant ID
#   D365FO_MCP_AUTH_BASE_URL - Base URL (will be auto-populated with FQDN after deployment)
#
# Option 2: API Key Authentication
#   D365FO_MCP_API_KEY_VALUE - Secure API key for authentication

# Validate authentication configuration
if [ -z "$D365FO_MCP_API_KEY_VALUE" ] && [ -z "$D365FO_MCP_AUTH_CLIENT_ID" ]; then
    echo "WARNING: No MCP authentication configured!"
    echo "For internet-exposed deployments, you must configure one of:"
    echo "  1. OAuth: D365FO_MCP_AUTH_CLIENT_ID, D365FO_MCP_AUTH_CLIENT_SECRET, D365FO_MCP_AUTH_TENANT_ID"
    echo "  2. API Key: D365FO_MCP_API_KEY_VALUE"
    echo ""
    read -p "Continue without authentication? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Validate OAuth credentials if CLIENT_ID is provided
if [ -n "$D365FO_MCP_AUTH_CLIENT_ID" ]; then
    : "${D365FO_MCP_AUTH_CLIENT_SECRET:?Error: D365FO_MCP_AUTH_CLIENT_SECRET is required when D365FO_MCP_AUTH_CLIENT_ID is set}"
    : "${D365FO_MCP_AUTH_TENANT_ID:?Error: D365FO_MCP_AUTH_TENANT_ID is required when D365FO_MCP_AUTH_CLIENT_ID is set}"
fi

# D365 F&O Configuration (optional - can be configured later via container app settings)
# Only validate CLIENT_SECRET if other credentials are provided
if [ -n "$D365FO_CLIENT_ID" ] || [ -n "$D365FO_TENANT_ID" ]; then
    : "${D365FO_CLIENT_SECRET:?Error: D365FO_CLIENT_SECRET is required when D365FO_CLIENT_ID or D365FO_TENANT_ID is set}"
fi

echo "=== Azure Container Apps Deployment ==="
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"
echo "Container App Environment: $CONTAINER_APP_ENV"
echo "Container App Name: $CONTAINER_APP_NAME"
echo "Image: $IMAGE"
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "Error: Azure CLI is not installed. Please install it from https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check if logged in
echo "Checking Azure login status..."
if ! az account show &> /dev/null; then
    echo "Error: Not logged in to Azure. Please run 'az login' first."
    exit 1
fi

echo "Logged in as: $(az account show --query user.name -o tsv)"
echo "Subscription: $(az account show --query name -o tsv)"
echo ""

# Create resource group if it doesn't exist
echo "Creating resource group (if not exists)..."
az group create \
    --name "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --output none

# Create Container App Environment if it doesn't exist
echo "Creating Container App Environment (if not exists)..."
if ! az containerapp env show --name "$CONTAINER_APP_ENV" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
    az containerapp env create \
        --name "$CONTAINER_APP_ENV" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --output none
    echo "Container App Environment created."
else
    echo "Container App Environment already exists."
fi

# Build secrets array
SECRETS=()
if [ -n "$D365FO_CLIENT_SECRET" ]; then
    SECRETS+=("d365fo-client-secret=$D365FO_CLIENT_SECRET")
fi
if [ -n "$D365FO_MCP_AUTH_CLIENT_SECRET" ]; then
    SECRETS+=("mcp-auth-client-secret=$D365FO_MCP_AUTH_CLIENT_SECRET")
fi
if [ -n "$D365FO_MCP_API_KEY_VALUE" ]; then
    SECRETS+=("mcp-api-key=$D365FO_MCP_API_KEY_VALUE")
fi

# Build environment variables array
ENV_VARS=()

# MCP Server configuration (always set)
ENV_VARS+=("D365FO_MCP_TRANSPORT=$D365FO_MCP_TRANSPORT")
ENV_VARS+=("D365FO_MCP_HTTP_HOST=$D365FO_MCP_HTTP_HOST")
ENV_VARS+=("D365FO_MCP_HTTP_PORT=$D365FO_MCP_HTTP_PORT")

# MCP Authentication configuration
if [ -n "$D365FO_MCP_AUTH_CLIENT_ID" ]; then
    ENV_VARS+=("D365FO_MCP_AUTH_CLIENT_ID=$D365FO_MCP_AUTH_CLIENT_ID")
    ENV_VARS+=("D365FO_MCP_AUTH_CLIENT_SECRET=secretref:mcp-auth-client-secret")
    ENV_VARS+=("D365FO_MCP_AUTH_TENANT_ID=$D365FO_MCP_AUTH_TENANT_ID")
    # BASE_URL will be set after getting FQDN
fi
if [ -n "$D365FO_MCP_API_KEY_VALUE" ]; then
    ENV_VARS+=("D365FO_MCP_API_KEY_VALUE=secretref:mcp-api-key")
fi

# D365 F&O configuration (optional)
if [ -n "$D365FO_BASE_URL" ]; then
    ENV_VARS+=("D365FO_BASE_URL=$D365FO_BASE_URL")
fi
if [ -n "$D365FO_CLIENT_ID" ]; then
    ENV_VARS+=("D365FO_CLIENT_ID=$D365FO_CLIENT_ID")
fi
if [ -n "$D365FO_TENANT_ID" ]; then
    ENV_VARS+=("D365FO_TENANT_ID=$D365FO_TENANT_ID")
fi
if [ -n "$D365FO_CLIENT_SECRET" ]; then
    ENV_VARS+=("D365FO_CLIENT_SECRET=secretref:d365fo-client-secret")
fi

# Deploy or update Container App
echo ""
echo "Deploying Container App..."
if az containerapp show --name "$CONTAINER_APP_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
    echo "Updating existing Container App..."
    UPDATE_CMD="az containerapp update \
        --name \"$CONTAINER_APP_NAME\" \
        --resource-group \"$RESOURCE_GROUP\" \
        --image \"$IMAGE\""

    if [ ${#ENV_VARS[@]} -gt 0 ]; then
        UPDATE_CMD="$UPDATE_CMD --set-env-vars"
        for env_var in "${ENV_VARS[@]}"; do
            UPDATE_CMD="$UPDATE_CMD \"$env_var\""
        done
    fi

    UPDATE_CMD="$UPDATE_CMD --output none"
    eval "$UPDATE_CMD"
else
    echo "Creating new Container App..."
    CREATE_CMD="az containerapp create \
        --name \"$CONTAINER_APP_NAME\" \
        --resource-group \"$RESOURCE_GROUP\" \
        --environment \"$CONTAINER_APP_ENV\" \
        --image \"$IMAGE\" \
        --target-port $D365FO_MCP_HTTP_PORT \
        --ingress external \
        --min-replicas 1 \
        --max-replicas 3 \
        --cpu 0.5 \
        --memory 1.0Gi"

    if [ ${#SECRETS[@]} -gt 0 ]; then
        CREATE_CMD="$CREATE_CMD --secrets"
        for secret in "${SECRETS[@]}"; do
            CREATE_CMD="$CREATE_CMD \"$secret\""
        done
    fi

    if [ ${#ENV_VARS[@]} -gt 0 ]; then
        CREATE_CMD="$CREATE_CMD --env-vars"
        for env_var in "${ENV_VARS[@]}"; do
            CREATE_CMD="$CREATE_CMD \"$env_var\""
        done
    fi

    CREATE_CMD="$CREATE_CMD --output none"
    eval "$CREATE_CMD"
fi

# Get the FQDN
FQDN=$(az containerapp show \
    --name "$CONTAINER_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query properties.configuration.ingress.fqdn \
    -o tsv)

# Update BASE_URL for OAuth if configured
if [ -n "$D365FO_MCP_AUTH_CLIENT_ID" ]; then
    echo ""
    echo "Updating MCP OAuth BASE_URL with FQDN..."
    az containerapp update \
        --name "$CONTAINER_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --set-env-vars "D365FO_MCP_AUTH_BASE_URL=https://$FQDN" \
        --output none
fi

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Container App URL: https://$FQDN"
echo ""

# Display authentication information
if [ -n "$D365FO_MCP_AUTH_CLIENT_ID" ]; then
    echo "Authentication: OAuth (Azure AD)"
    echo "  Client ID: $D365FO_MCP_AUTH_CLIENT_ID"
    echo "  Tenant ID: $D365FO_MCP_AUTH_TENANT_ID"
    echo "  Base URL: https://$FQDN"
    echo ""
    echo "IMPORTANT: Configure redirect URI in Azure AD App Registration:"
    echo "  https://$FQDN/auth/callback"
elif [ -n "$D365FO_MCP_API_KEY_VALUE" ]; then
    echo "Authentication: API Key"
    echo "  API Key: (stored as secret 'mcp-api-key')"
    echo ""
    echo "To authenticate, include header: X-API-Key: your-api-key-value"
else
    echo "WARNING: No authentication configured - endpoint is publicly accessible!"
fi

echo ""
echo "To view logs, run:"
echo "  az containerapp logs show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --follow"
echo ""
echo "To test the MCP server endpoint:"
echo "  curl https://$FQDN/"
echo ""
