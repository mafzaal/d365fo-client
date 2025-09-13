# FastMCP D365FO Server - Production Deployment Guide

This guide provides comprehensive instructions for deploying the FastMCP D365FO server in production environments with HTTP and SSE transports.

## Table of Contents

1. [Production Architecture](#production-architecture)
2. [Deployment Options](#deployment-options)
3. [Configuration Management](#configuration-management)
4. [Security Considerations](#security-considerations)
5. [Monitoring and Logging](#monitoring-and-logging)
6. [Load Balancing and Scaling](#load-balancing-and-scaling)
7. [Troubleshooting](#troubleshooting)

## Production Architecture

### Recommended Production Setup

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │  Reverse Proxy  │    │   Application   │
│   (Azure LB/    │    │   (nginx/       │    │    Servers      │
│   AWS ALB)      │────│   Traefik)      │────│                 │
└─────────────────┘    └─────────────────┘    │ FastMCP Server  │
                                              │ (Multiple       │
                                              │  Instances)     │
                                              └─────────────────┘
                                                       │
                                              ┌─────────────────┐
                                              │   D365 F&O      │
                                              │   Environment   │
                                              └─────────────────┘
```

### Transport Selection by Use Case

| Use Case | Transport | Port | Notes |
|----------|-----------|------|-------|
| API Integration | HTTP | 8000 | RESTful MCP-over-HTTP |
| Real-time Dashboards | SSE | 8001 | Server-Sent Events |
| Development/Testing | stdio | N/A | Direct MCP protocol |

## Deployment Options

### 1. Docker Deployment (Recommended)

#### Dockerfile

```dockerfile
FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install d365fo-client
RUN pip install d365fo-client

# Create non-root user
RUN useradd -m -u 1000 d365fo && chown d365fo:d365fo /app
USER d365fo

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default to HTTP transport
EXPOSE 8000
CMD ["d365fo-fastmcp-server", "--transport", "http", "--port", "8000", "--host", "0.0.0.0"]
```

#### Docker Compose

```yaml
version: '3.8'

services:
  d365fo-fastmcp-http:
    build: .
    ports:
      - "8000:8000"
    environment:
      - D365FO_BASE_URL=${D365FO_BASE_URL}
      - D365FO_CLIENT_ID=${D365FO_CLIENT_ID}
      - D365FO_CLIENT_SECRET=${D365FO_CLIENT_SECRET}
      - D365FO_TENANT_ID=${D365FO_TENANT_ID}
      - D365FO_LOG_LEVEL=INFO
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - d365fo-network

  d365fo-fastmcp-sse:
    build: .
    ports:
      - "8001:8001"
    environment:
      - D365FO_BASE_URL=${D365FO_BASE_URL}
      - D365FO_CLIENT_ID=${D365FO_CLIENT_ID}
      - D365FO_CLIENT_SECRET=${D365FO_CLIENT_SECRET}
      - D365FO_TENANT_ID=${D365FO_TENANT_ID}
      - D365FO_LOG_LEVEL=INFO
    restart: unless-stopped
    command: ["d365fo-fastmcp-server", "--transport", "sse", "--port", "8001", "--host", "0.0.0.0"]
    networks:
      - d365fo-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - d365fo-fastmcp-http
      - d365fo-fastmcp-sse
    networks:
      - d365fo-network

networks:
  d365fo-network:
    driver: bridge
```

### 2. Kubernetes Deployment

#### Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: d365fo-fastmcp-http
  labels:
    app: d365fo-fastmcp
    transport: http
spec:
  replicas: 3
  selector:
    matchLabels:
      app: d365fo-fastmcp
      transport: http
  template:
    metadata:
      labels:
        app: d365fo-fastmcp
        transport: http
    spec:
      containers:
      - name: fastmcp-server
        image: d365fo-client:latest
        command: ["d365fo-fastmcp-server"]
        args: ["--transport", "http", "--port", "8000", "--host", "0.0.0.0"]
        ports:
        - containerPort: 8000
        env:
        - name: D365FO_BASE_URL
          valueFrom:
            configMapKeyRef:
              name: d365fo-config
              key: base-url
        - name: D365FO_CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: d365fo-credentials
              key: client-id
        - name: D365FO_CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: d365fo-credentials
              key: client-secret
        - name: D365FO_TENANT_ID
          valueFrom:
            secretKeyRef:
              name: d365fo-credentials
              key: tenant-id
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: d365fo-fastmcp-http-service
spec:
  selector:
    app: d365fo-fastmcp
    transport: http
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

#### ConfigMap and Secrets

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: d365fo-config
data:
  base-url: "https://your-d365fo-environment.dynamics.com"
  log-level: "INFO"
  cache-dir: "/app/cache"
---
apiVersion: v1
kind: Secret
metadata:
  name: d365fo-credentials
type: Opaque
data:
  client-id: <base64-encoded-client-id>
  client-secret: <base64-encoded-client-secret>
  tenant-id: <base64-encoded-tenant-id>
```

### 3. Azure Container Instances

```bash
#!/bin/bash

# Create resource group
az group create --name d365fo-mcp --location eastus

# Create container instance for HTTP transport
az container create \
    --resource-group d365fo-mcp \
    --name d365fo-fastmcp-http \
    --image d365fo-client:latest \
    --ports 8000 \
    --dns-name-label d365fo-mcp-http \
    --environment-variables \
        D365FO_BASE_URL="https://your-environment.dynamics.com" \
        D365FO_LOG_LEVEL="INFO" \
    --secure-environment-variables \
        D365FO_CLIENT_ID="your-client-id" \
        D365FO_CLIENT_SECRET="your-client-secret" \
        D365FO_TENANT_ID="your-tenant-id" \
    --command-line "d365fo-fastmcp-server --transport http --port 8000 --host 0.0.0.0"

# Create container instance for SSE transport
az container create \
    --resource-group d365fo-mcp \
    --name d365fo-fastmcp-sse \
    --image d365fo-client:latest \
    --ports 8001 \
    --dns-name-label d365fo-mcp-sse \
    --environment-variables \
        D365FO_BASE_URL="https://your-environment.dynamics.com" \
        D365FO_LOG_LEVEL="INFO" \
    --secure-environment-variables \
        D365FO_CLIENT_ID="your-client-id" \
        D365FO_CLIENT_SECRET="your-client-secret" \
        D365FO_TENANT_ID="your-tenant-id" \
    --command-line "d365fo-fastmcp-server --transport sse --port 8001 --host 0.0.0.0"
```

## Configuration Management

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `D365FO_BASE_URL` | Yes | - | D365 F&O environment URL |
| `D365FO_CLIENT_ID` | No* | - | Azure AD Client ID |
| `D365FO_CLIENT_SECRET` | No* | - | Azure AD Client Secret |
| `D365FO_TENANT_ID` | No* | - | Azure AD Tenant ID |
| `D365FO_LOG_LEVEL` | No | INFO | Logging level |
| `D365FO_CACHE_DIR` | No | Platform default | Cache directory |
| `D365FO_TIMEOUT` | No | 30 | Request timeout (seconds) |
| `D365FO_MAX_CONNECTIONS` | No | 10 | Max concurrent connections |

*Not required when using Azure Default Credentials (Managed Identity)

### Production Configuration

```bash
# Production environment variables
export D365FO_BASE_URL="https://prod.dynamics.com"
export D365FO_LOG_LEVEL="INFO"
export D365FO_CACHE_DIR="/app/cache"
export D365FO_TIMEOUT="60"
export D365FO_MAX_CONNECTIONS="20"

# Security settings
export D365FO_VERIFY_SSL="true"
export D365FO_USE_LABEL_CACHE="true"
export D365FO_LABEL_CACHE_EXPIRY_MINUTES="120"

# Performance tuning
export UVICORN_WORKERS="4"
export UVICORN_WORKER_CLASS="uvicorn.workers.UvicornWorker"
```

### Azure Key Vault Integration

```bash
# Use Azure Key Vault for credential management
export D365FO_CREDENTIAL_SOURCE="keyvault"
export D365FO_KEYVAULT_URL="https://your-keyvault.vault.azure.net/"

# Key Vault secret names (optional, defaults shown)
export D365FO_KEYVAULT_CLIENT_ID_SECRET="d365fo-client-id"
export D365FO_KEYVAULT_CLIENT_SECRET_SECRET="d365fo-client-secret"
export D365FO_KEYVAULT_TENANT_ID_SECRET="d365fo-tenant-id"
```

## Security Considerations

### 1. Authentication and Authorization

#### Azure Managed Identity (Recommended)

```yaml
# Kubernetes with Managed Identity
apiVersion: v1
kind: Pod
metadata:
  name: d365fo-fastmcp
  labels:
    aadpodidbinding: d365fo-identity
spec:
  containers:
  - name: fastmcp-server
    image: d365fo-client:latest
    env:
    - name: D365FO_BASE_URL
      value: "https://your-environment.dynamics.com"
    # No credential environment variables needed
```

#### Service Principal

```bash
# Create service principal for D365FO access
az ad sp create-for-rbac \
    --name "d365fo-mcp-server" \
    --role "Dynamics 365 Finance and Operations API access" \
    --scopes "/subscriptions/{subscription-id}/resourceGroups/{resource-group}"
```

### 2. Network Security

#### Nginx Reverse Proxy Configuration

```nginx
upstream d365fo_http {
    server d365fo-fastmcp-http:8000;
}

upstream d365fo_sse {
    server d365fo-fastmcp-sse:8001;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    # HTTP transport
    location /api/ {
        proxy_pass http://d365fo_http/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Security headers
        add_header X-Content-Type-Options nosniff;
        add_header X-Frame-Options DENY;
        add_header X-XSS-Protection "1; mode=block";
    }
    
    # SSE transport
    location /events/ {
        proxy_pass http://d365fo_sse/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # SSE specific settings
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
        proxy_buffering off;
        proxy_cache off;
    }
}
```

### 3. Firewall Rules

```bash
# Azure Network Security Group rules
az network nsg rule create \
    --resource-group d365fo-mcp \
    --nsg-name d365fo-nsg \
    --name allow-https \
    --protocol Tcp \
    --priority 1000 \
    --destination-port-ranges 443 \
    --access Allow

# Restrict source IPs to trusted networks
az network nsg rule create \
    --resource-group d365fo-mcp \
    --nsg-name d365fo-nsg \
    --name allow-api-access \
    --protocol Tcp \
    --priority 1100 \
    --destination-port-ranges 8000 8001 \
    --source-address-prefixes 10.0.0.0/8 192.168.0.0/16 \
    --access Allow
```

## Monitoring and Logging

### 1. Application Monitoring

#### Prometheus Metrics

```python
# Custom metrics endpoint for FastMCP server
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('d365fo_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('d365fo_request_duration_seconds', 'Request duration')

@app.route('/metrics')
def metrics():
    return generate_latest()
```

#### Health Check Endpoint

```python
# Built-in health check (automatically available)
# GET /health returns:
{
    "status": "healthy",
    "timestamp": "2025-01-09T10:30:00Z",
    "version": "0.2.3",
    "transport": "http",
    "uptime_seconds": 3600,
    "d365fo_connection": "ok"
}
```

### 2. Log Aggregation

#### Structured Logging

```bash
# Configure structured JSON logging
export D365FO_LOG_FORMAT="json"
export D365FO_LOG_LEVEL="INFO"

# Output example:
{
    "timestamp": "2025-01-09T10:30:00Z",
    "level": "INFO",
    "logger": "d365fo_client.mcp.fastmcp_server",
    "message": "Tool executed successfully",
    "tool_name": "d365fo_query_entities",
    "execution_time_ms": 150,
    "request_id": "req_123456"
}
```

#### ELK Stack Integration

```yaml
# Docker Compose with ELK
version: '3.8'
services:
  d365fo-fastmcp:
    # ... server configuration
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "service=d365fo-fastmcp"

  elasticsearch:
    image: elasticsearch:7.17.0
    environment:
      - discovery.type=single-node
    ports:
      - "9200:9200"

  logstash:
    image: logstash:7.17.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch

  kibana:
    image: kibana:7.17.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
```

### 3. Azure Monitor Integration

```bash
# Enable Azure Monitor for Container Instances
az monitor log-analytics workspace create \
    --resource-group d365fo-mcp \
    --workspace-name d365fo-logs

# Configure container to send logs
az container create \
    --resource-group d365fo-mcp \
    --name d365fo-fastmcp \
    --log-analytics-workspace d365fo-logs \
    # ... other configuration
```

## Load Balancing and Scaling

### 1. Horizontal Scaling

#### Kubernetes Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: d365fo-fastmcp-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: d365fo-fastmcp-http
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 2. Load Balancer Configuration

#### Azure Application Gateway

```bash
# Create Application Gateway with WAF
az network application-gateway create \
    --name d365fo-appgw \
    --location eastus \
    --resource-group d365fo-mcp \
    --sku WAF_v2 \
    --public-ip-address d365fo-pip \
    --vnet-name d365fo-vnet \
    --subnet appgw-subnet \
    --servers d365fo-mcp-http.eastus.azurecontainer.io \
              d365fo-mcp-sse.eastus.azurecontainer.io
```

### 3. Session Affinity

For SSE connections, configure session affinity:

```nginx
upstream d365fo_sse {
    ip_hash;  # Session affinity for SSE connections
    server d365fo-sse-1:8001;
    server d365fo-sse-2:8001;
    server d365fo-sse-3:8001;
}
```

## Troubleshooting

### Common Issues

#### 1. Connection Timeouts

```bash
# Increase timeout settings
export D365FO_TIMEOUT="120"
export UVICORN_TIMEOUT_KEEP_ALIVE="120"

# Check network connectivity
curl -v https://your-d365fo-environment.dynamics.com/data/$metadata
```

#### 2. Memory Issues

```bash
# Monitor memory usage
docker stats d365fo-fastmcp

# Increase container memory limits
docker run --memory=1g d365fo-client:latest

# Kubernetes resource limits
resources:
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

#### 3. Authentication Failures

```bash
# Test Azure AD authentication
az login --service-principal \
    --username $D365FO_CLIENT_ID \
    --password $D365FO_CLIENT_SECRET \
    --tenant $D365FO_TENANT_ID

# Verify token acquisition
python -c "
from azure.identity import ClientSecretCredential
cred = ClientSecretCredential('$D365FO_TENANT_ID', '$D365FO_CLIENT_ID', '$D365FO_CLIENT_SECRET')
token = cred.get_token('https://your-environment.dynamics.com/.default')
print('Token acquired successfully')
"
```

### Monitoring Commands

```bash
# Check server health
curl http://localhost:8000/health

# Test MCP protocol
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | \
curl -X POST -H "Content-Type: application/json" \
     -d @- http://localhost:8000/mcp

# Monitor logs
docker logs -f d365fo-fastmcp

# Check resource usage
kubectl top pods -l app=d365fo-fastmcp
```

### Performance Tuning

#### 1. Connection Pool Optimization

```bash
# Optimize connection settings
export D365FO_MAX_CONNECTIONS="50"
export D365FO_CONNECTION_POOL_SIZE="20"
export D365FO_CONNECTION_TIMEOUT="30"
```

#### 2. Cache Configuration

```bash
# Enable and tune caching
export D365FO_USE_LABEL_CACHE="true"
export D365FO_LABEL_CACHE_EXPIRY_MINUTES="240"
export D365FO_METADATA_CACHE_STRATEGY="smart_sync"
```

#### 3. Uvicorn Workers

```bash
# Multi-worker configuration
d365fo-fastmcp-server \
    --transport http \
    --port 8000 \
    --host 0.0.0.0 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker
```

## Support and Maintenance

### Regular Maintenance Tasks

```bash
# Update to latest version
pip install --upgrade d365fo-client

# Clear cache periodically
rm -rf /app/cache/*

# Rotate logs
logrotate /etc/logrotate.d/d365fo-fastmcp
```

### Backup and Recovery

```bash
# Backup configuration and cache
tar -czf d365fo-backup-$(date +%Y%m%d).tar.gz \
    /app/config \
    /app/cache

# Automated backup script
#!/bin/bash
BACKUP_DIR="/backup"
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf "$BACKUP_DIR/d365fo-backup-$DATE.tar.gz" /app/cache
find "$BACKUP_DIR" -name "d365fo-backup-*.tar.gz" -mtime +7 -delete
```

This production deployment guide provides a comprehensive foundation for deploying FastMCP D365FO servers in enterprise environments with proper security, monitoring, and scalability considerations.