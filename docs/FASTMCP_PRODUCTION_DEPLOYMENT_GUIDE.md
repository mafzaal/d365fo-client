# FastMCP D365FO Server - Production Deployment Guide

This guide provides comprehensive instructions for deploying the FastMCP D365FO server in production environments with enhanced Phase 4 features including stateless HTTP mode, JSON response support, and performance optimizations.

## Phase 4 Production Features ✅

### New Production Capabilities
- **✅ Stateless HTTP Mode**: Horizontal scaling with load balancer support
- **✅ JSON Response Support**: API gateway compatible responses  
- **✅ Performance Monitoring**: Built-in metrics and health checks
- **✅ Enhanced Configuration**: Environment-based production settings
- **✅ Connection Pooling**: Optimized D365FO client management
- **✅ Request Limiting**: Configurable concurrent request controls

## Table of Contents

1. [Phase 4 Production Features](#phase-4-production-features)
2. [Production Architecture](#production-architecture)
3. [Deployment Strategies](#deployment-strategies)
4. [Configuration Management](#configuration-management)
5. [Performance Optimization](#performance-optimization)
6. [Security Considerations](#security-considerations)
7. [Monitoring and Health Checks](#monitoring-and-health-checks)
8. [Load Balancing and Scaling](#load-balancing-and-scaling)
9. [Container Deployments](#container-deployments)
10. [Troubleshooting](#troubleshooting)

## Production Architecture

### Enhanced Production Setup with Phase 4 Features

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │  Reverse Proxy  │    │   Application   │
│   (Azure LB/    │    │   (nginx/       │    │    Servers      │
│   AWS ALB)      │────│   Traefik)      │────│                 │
└─────────────────┘    └─────────────────┘    │ FastMCP Server  │
                                              │ (Stateless Mode)│
┌─────────────────┐                           │ Multiple        │
│  Health Checks  │                           │ Instances       │
│  & Monitoring   │───────────────────────────│ w/ Perf Monitor │
└─────────────────┘                           └─────────────────┘
                                                       │
                                              ┌─────────────────┐
                                              │   D365 F&O      │
                                              │   Environment   │
                                              └─────────────────┘
```

### Transport Selection by Use Case

| Use Case | Transport | Mode | Features | Best For |
|----------|-----------|------|----------|----------|
| Production API | HTTP | Stateless + JSON | Load balancing, auto-scaling | Enterprise deployments |
| Real-time Apps | SSE | Stateful | Server-sent events | Dashboards, monitoring |
| High Availability | HTTP | Stateless | Session independence | Cloud-native apps |
| Development | stdio | N/A | Direct MCP protocol | Local development |

## Deployment Strategies

### 1. Stateless Production Deployment (Recommended)

```bash
# High-availability stateless deployment
d365fo-fastmcp-server --transport http --host 0.0.0.0 --port 8000 --stateless --json-response
```

**Benefits:**
- Horizontal scaling with load balancer
- No server-side session state
- Perfect for cloud deployments
- Auto-scaling compatible

### 2. Development Deployment

```bash
# Local development
d365fo-fastmcp-server --transport stdio

# Web testing
d365fo-fastmcp-server --transport sse --port 8000 --debug
```

### 3. Stateful Production Deployment

```bash
# Traditional stateful deployment
d365fo-fastmcp-server --transport http --host 0.0.0.0 --port 8000
```

**Use Cases:**
- Small to medium scale deployments
- Session persistence required
- Single-region deployments

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

## Performance Optimization

### Built-in Performance Features

The Phase 4 FastMCP server includes comprehensive performance optimizations:

#### 1. Connection Pooling
```bash
# Configure connection pool size
export MCP_CONNECTION_POOL_SIZE="10"  # Default: 5

# Monitor pool utilization
d365fo_get_server_performance
```

#### 2. Request Limiting
```bash
# Limit concurrent requests to prevent overload
export D365FO_MAX_CONCURRENT_REQUESTS="20"  # Default: 10

# Set request timeout
export D365FO_REQUEST_TIMEOUT="45"  # Default: 30 seconds
```

#### 3. Performance Monitoring
```bash
# Enable detailed performance tracking
export MCP_PERFORMANCE_MONITORING="true"

# Get real-time performance stats
curl -X POST http://localhost:8000/tools/d365fo_get_server_performance

# Reset performance counters
curl -X POST http://localhost:8000/tools/d365fo_reset_performance_stats
```

### Performance Metrics

The server tracks the following metrics:

- **Request Volume**: Total requests processed
- **Error Rate**: Percentage of failed requests  
- **Response Times**: Average, min, max, P95 response times
- **Concurrent Requests**: Current active request count
- **Connection Pool**: Pool hits/misses and utilization
- **Memory Usage**: Cache size and memory consumption

### Optimization Guidelines

#### Small Scale (< 100 requests/min)
```bash
export D365FO_MAX_CONCURRENT_REQUESTS="5"
export MCP_CONNECTION_POOL_SIZE="3"
export D365FO_REQUEST_TIMEOUT="30"
export MCP_CACHE_SIZE_LIMIT="50"
```

#### Medium Scale (100-1000 requests/min)
```bash
export D365FO_MAX_CONCURRENT_REQUESTS="15"
export MCP_CONNECTION_POOL_SIZE="8"
export D365FO_REQUEST_TIMEOUT="45"
export MCP_CACHE_SIZE_LIMIT="150"
```

#### Large Scale (> 1000 requests/min)
```bash
export D365FO_MAX_CONCURRENT_REQUESTS="30"
export MCP_CONNECTION_POOL_SIZE="15"
export D365FO_REQUEST_TIMEOUT="60"
export MCP_CACHE_SIZE_LIMIT="300"
export D365FO_HTTP_STATELESS="true"  # Enable for horizontal scaling
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

## Monitoring and Health Checks

### Built-in Health Monitoring

The FastMCP server provides comprehensive health monitoring capabilities:

#### 1. Performance Dashboard Tools

```bash
# Get comprehensive server performance statistics
d365fo_get_server_performance

# Example response:
{
  "server_performance": {
    "server_uptime_seconds": 3600,
    "total_requests": 1250,
    "total_errors": 12,
    "error_rate": 0.96,
    "avg_response_time_ms": 245.3,
    "current_active_requests": 3,
    "max_concurrent_requests": 20,
    "stateless_mode": true,
    "json_response_mode": true
  },
  "client_health": {
    "default": {
      "healthy": true,
      "last_checked": "2024-01-15T10:30:00Z"
    }
  }
}
```

#### 2. Server Configuration Monitoring

```bash
# Get current server configuration
d365fo_get_server_config

# Monitor configuration changes
{
  "server_config": {
    "server_version": "0.2.3",
    "stateless_mode": true,
    "json_response_mode": true,
    "max_concurrent_requests": 20,
    "request_timeout": 45
  }
}
```

#### 3. Health Check Endpoints

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed health with D365FO connectivity
curl -X POST http://localhost:8000/tools/d365fo_test_connection

# Performance metrics endpoint
curl http://localhost:8000/metrics
```

### External Monitoring Integration

#### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'd365fo-mcp'
    static_configs:
      - targets: ['d365fo-mcp-server:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
    scrape_timeout: 5s
```

#### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "D365FO MCP Server Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(mcp_requests_total[5m])",
            "legendFormat": "Requests/sec"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph", 
        "targets": [
          {
            "expr": "rate(mcp_errors_total[5m]) / rate(mcp_requests_total[5m]) * 100",
            "legendFormat": "Error %"
          }
        ]
      }
    ]
  }
}
```

### Alerting Rules

#### Critical Alerts

```yaml
# alerting-rules.yml
groups:
- name: d365fo-mcp-critical
  rules:
  - alert: MCPServerDown
    expr: up{job="d365fo-mcp"} == 0
    for: 30s
    labels:
      severity: critical
    annotations:
      summary: "MCP Server is down"
      
  - alert: HighErrorRate
    expr: rate(mcp_errors_total[5m]) / rate(mcp_requests_total[5m]) > 0.1
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"

  - alert: HighResponseTime  
    expr: mcp_response_time_p95 > 5000
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High response time detected"
```

### Logging Configuration

#### Structured Logging

```bash
# Enable structured JSON logging
export D365FO_LOG_LEVEL="INFO"
export MCP_LOG_FORMAT="json"

# Log rotation settings
export MCP_LOG_MAX_SIZE="100MB"
export MCP_LOG_BACKUP_COUNT="10"
```

#### Log Analysis Examples

```bash
# Monitor error patterns
grep "ERROR" ~/.d365fo-mcp/logs/fastmcp-server.log | tail -20

# Performance analysis
grep "execution_time" ~/.d365fo-mcp/logs/fastmcp-server.log | awk '{print $5}' | sort -n

# Connection monitoring
grep "connection" ~/.d365fo-mcp/logs/fastmcp-server.log | grep -v "successful"
```

## Load Balancing and Scaling

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

### Phase 4 Production Issues

#### 1. Stateless Mode Issues

```bash
# Check stateless mode configuration
d365fo_get_server_config

# Verify session cleanup
d365fo_get_server_performance

# Common stateless issues:
# - Load balancer not routing correctly
# - Session affinity enabled (should be disabled)
# - Client attempting to maintain sessions

# Debug stateless mode
export D365FO_LOG_LEVEL="DEBUG"
grep "stateless" ~/.d365fo-mcp/logs/fastmcp-server.log
```

#### 2. Performance Degradation

```bash
# Monitor real-time performance
watch -n 5 'curl -s -X POST http://localhost:8000/tools/d365fo_get_server_performance | jq .server_performance'

# Check for bottlenecks
# High response times
if [ "$(curl -s http://localhost:8000/tools/d365fo_get_server_performance | jq '.server_performance.avg_response_time_ms')" -gt 1000 ]; then
    echo "Response time degradation detected"
    # Reduce concurrent requests
    export D365FO_MAX_CONCURRENT_REQUESTS="5"
fi

# Memory issues
if [ "$(docker stats --no-stream --format 'table {{.MemPerc}}' d365fo-mcp | tail -1 | sed 's/%//')" -gt 80 ]; then
    echo "High memory usage detected"
    # Reset performance stats and cleanup
    curl -X POST http://localhost:8000/tools/d365fo_reset_performance_stats
fi
```

#### 3. Connection Pool Exhaustion

```bash
# Monitor connection pool
d365fo_get_server_performance | jq '.server_performance.connection_pool_stats'

# Signs of pool exhaustion:
# - High pool misses
# - Connection errors increasing
# - Requests timing out

# Remediation
export MCP_CONNECTION_POOL_SIZE="15"  # Increase pool size
export D365FO_REQUEST_TIMEOUT="30"       # Reduce timeout
export D365FO_MAX_CONCURRENT_REQUESTS="10"  # Limit concurrent requests

# Restart with new settings
docker restart d365fo-mcp-server
```

### Common Production Issues

#### 1. Connection Timeouts

```bash
# Increase timeout settings for production workloads
export D365FO_REQUEST_TIMEOUT="120"      # 2 minutes for complex operations
export MCP_CONNECTION_POOL_SIZE="20"  # Larger pool for high throughput

# Test D365FO connectivity
curl -v https://your-d365fo-environment.dynamics.com/data/\$metadata

# Check network latency
ping your-d365fo-environment.dynamics.com
```

#### 2. Authentication Issues

```bash
# Test Azure AD authentication
az login --service-principal \
    --username $D365FO_CLIENT_ID \
    --password $D365FO_CLIENT_SECRET \
    --tenant $D365FO_TENANT_ID

# Verify D365FO access
curl -H "Authorization: Bearer $(az account get-access-token --resource https://your-environment.dynamics.com --query accessToken -o tsv)" \
     https://your-environment.dynamics.com/data/\$metadata

# Check token refresh issues
grep "token" ~/.d365fo-mcp/logs/fastmcp-server.log | tail -10
```

#### 3. High Memory Usage

```bash
# Monitor memory patterns
docker stats --no-stream d365fo-mcp-server

# Kubernetes memory monitoring  
kubectl top pods -l app=d365fo-mcp-server

# Optimize memory usage
export MCP_CACHE_SIZE_LIMIT="100"     # Reduce cache size
export MCP_MAX_REQUEST_HISTORY="500"  # Reduce request history

# Enable memory-efficient mode
export D365FO_HTTP_STATELESS="true"      # Stateless mode uses less memory
```

### Health Check Diagnostics

#### Built-in Health Checks

```bash
# Comprehensive health check
curl -s http://localhost:8000/health | jq '.'

# D365FO connectivity test
curl -s -X POST http://localhost:8000/tools/d365fo_test_connection | jq '.'

# Performance health check
curl -s -X POST http://localhost:8000/tools/d365fo_get_server_performance | jq '.server_performance | {error_rate, avg_response_time_ms, current_active_requests}'
```

#### Custom Health Monitoring Script

```bash
#!/bin/bash
# health-check.sh

SERVER_URL="http://localhost:8000"
ALERT_THRESHOLD_ERROR_RATE=5.0
ALERT_THRESHOLD_RESPONSE_TIME=2000

# Get performance stats
STATS=$(curl -s -X POST $SERVER_URL/tools/d365fo_get_server_performance)
ERROR_RATE=$(echo $STATS | jq -r '.server_performance.error_rate')
RESPONSE_TIME=$(echo $STATS | jq -r '.server_performance.avg_response_time_ms')

# Check error rate
if (( $(echo "$ERROR_RATE > $ALERT_THRESHOLD_ERROR_RATE" | bc -l) )); then
    echo "ALERT: High error rate detected: $ERROR_RATE%"
    exit 1
fi

# Check response time
if (( $(echo "$RESPONSE_TIME > $ALERT_THRESHOLD_RESPONSE_TIME" | bc -l) )); then
    echo "ALERT: High response time detected: ${RESPONSE_TIME}ms"
    exit 1
fi

echo "Health check passed - Error rate: $ERROR_RATE%, Response time: ${RESPONSE_TIME}ms"
exit 0
```

### Performance Optimization

#### Production Tuning Guidelines

```bash
# High-traffic production environment
export D365FO_MAX_CONCURRENT_REQUESTS="50"
export MCP_CONNECTION_POOL_SIZE="25"
export D365FO_REQUEST_TIMEOUT="90"
export MCP_BATCH_SIZE="200"
export D365FO_HTTP_STATELESS="true"
export D365FO_HTTP_JSON="true"
export MCP_PERFORMANCE_MONITORING="true"

# Memory optimization
export MCP_CACHE_SIZE_LIMIT="200"
export MCP_MAX_REQUEST_HISTORY="2000"
export MCP_SESSION_CLEANUP_INTERVAL="180"  # 3 minutes

# Security hardening
export MCP_CORS_ORIGINS="https://yourdomain.com"
export D365FO_VERIFY_SSL="true"
export MCP_TOKEN_EXPIRY_BUFFER="10"
```

#### Load Testing

```bash
# Simple load test with curl
for i in {1..100}; do
  curl -s -X POST http://localhost:8000/tools/d365fo_test_connection &
done
wait

# Monitor performance during load test
watch -n 2 'curl -s -X POST http://localhost:8000/tools/d365fo_get_server_performance | jq .server_performance.current_active_requests'

# Apache Benchmark load test
ab -n 1000 -c 10 -H "Content-Type: application/json" \
   -p test-payload.json \
   http://localhost:8000/tools/d365fo_test_connection
```

### Logging and Debugging

#### Enhanced Logging Configuration

```bash
# Enable debug logging
export D365FO_LOG_LEVEL="DEBUG"

# Structured JSON logging for production
export MCP_LOG_FORMAT="json"

# Log aggregation friendly format
export MCP_LOG_INCLUDE_TIMESTAMP="true"
export MCP_LOG_INCLUDE_THREAD_ID="true"
```

#### Common Log Patterns

```bash
# Performance issues
grep "timeout\|slow\|performance" ~/.d365fo-mcp/logs/fastmcp-server.log

# Authentication problems
grep "auth\|token\|credential" ~/.d365fo-mcp/logs/fastmcp-server.log

# Connection issues
grep "connection\|pool\|client" ~/.d365fo-mcp/logs/fastmcp-server.log

# Memory and resource issues
grep "memory\|resource\|limit" ~/.d365fo-mcp/logs/fastmcp-server.log
```

### Recovery Procedures

#### Automatic Recovery

```bash
# Systemd service with automatic restart
# /etc/systemd/system/d365fo-mcp.service
[Unit]
Description=D365FO FastMCP Server
After=network.target

[Service]
Type=exec
User=mcpuser
Group=mcpuser
WorkingDirectory=/app
ExecStart=/app/.venv/bin/d365fo-fastmcp-server --transport http --host 0.0.0.0 --port 8000 --stateless
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

#### Manual Recovery Steps

```bash
# 1. Stop the server
docker stop d365fo-mcp-server

# 2. Clear cache if needed
rm -rf ~/.d365fo-mcp/cache/*

# 3. Check configuration
d365fo-fastmcp-server --help

# 4. Test D365FO connectivity
curl https://your-environment.dynamics.com/data/\$metadata

# 5. Restart with debug logging
docker run -e D365FO_LOG_LEVEL=DEBUG d365fo-mcp-server

# 6. Monitor startup
docker logs -f d365fo-mcp-server
```

## Production Checklist

### Pre-Deployment Validation

- [ ] **Environment Configuration**
  - [ ] D365FO_BASE_URL configured and accessible
  - [ ] Authentication method validated (Azure AD/Managed Identity)
  - [ ] Network connectivity to D365FO environment verified
  
- [ ] **Performance Configuration**
  - [ ] D365FO_MAX_CONCURRENT_REQUESTS set appropriately
  - [ ] D365FO_REQUEST_TIMEOUT configured for workload
  - [ ] MCP_CONNECTION_POOL_SIZE optimized
  - [ ] Memory limits configured
  
- [ ] **Security Configuration**
  - [ ] CORS origins restricted in production
  - [ ] SSL/TLS enabled for external access
  - [ ] Secrets properly managed (Key Vault/Kubernetes secrets)
  - [ ] Non-root container user configured

### Deployment Validation

- [ ] **Health Checks**
  - [ ] Health endpoint responding correctly
  - [ ] D365FO connectivity test passing
  - [ ] Performance metrics collection working
  
- [ ] **Load Testing**
  - [ ] Performance under expected load validated
  - [ ] Memory usage stable under load
  - [ ] Error rates within acceptable limits
  
- [ ] **Monitoring Setup**
  - [ ] Log aggregation configured
  - [ ] Performance monitoring enabled
  - [ ] Alerting rules configured
  - [ ] Dashboard created

### Post-Deployment Monitoring

- [ ] **Daily Checks**
  - [ ] Performance metrics review
  - [ ] Error rate monitoring
  - [ ] Resource utilization check
  
- [ ] **Weekly Maintenance**
  - [ ] Log rotation and cleanup
  - [ ] Performance statistics reset
  - [ ] Security updates review
  
- [ ] **Monthly Reviews**
  - [ ] Capacity planning assessment
  - [ ] Performance optimization opportunities
  - [ ] Disaster recovery testing

This comprehensive guide ensures successful Phase 4 FastMCP production deployments with enterprise-grade performance, monitoring, and reliability.

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