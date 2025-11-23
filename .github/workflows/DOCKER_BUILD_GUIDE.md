# Docker Build Workflow Guide

## Overview

The Docker build workflow supports **on-demand builds** from any branch with intelligent tagging based on the source branch or tag.

## Triggering Builds

### Automatic Triggers
- **Push to `main` branch**: Automatically builds and tags as `:latest`
- **Version tags (`v*`)**: Automatically builds and tags with semantic versions

### Manual Triggers (On-Demand)
- Navigate to: **Actions → Docker Build and Push → Run workflow**
- Select the branch you want to build from
- Click "Run workflow"

## Tagging Strategy

### Main Branch (`main`)
**Trigger**: Push to main or manual workflow_dispatch from main

**Tags generated**:
- `ghcr.io/[repo]:latest` ✅
- `ghcr.io/[repo]:main`
- `ghcr.io/[repo]:main-[short-sha]`

**Example**:
```
ghcr.io/yourusername/d365fo-client:latest
ghcr.io/yourusername/d365fo-client:main
ghcr.io/yourusername/d365fo-client:main-a1b2c3d
```

### Develop Branch (`develop`)
**Trigger**: Manual workflow_dispatch from develop branch

**Tags generated**:
- `ghcr.io/[repo]:develop` ✅
- `ghcr.io/[repo]:develop-[short-sha]`

**No `:latest` tag** - `:latest` remains unchanged ✅

**Example**:
```
ghcr.io/yourusername/d365fo-client:develop
ghcr.io/yourusername/d365fo-client:develop-x7y8z9a
```

### Feature Branches (`feature/my-feature`)
**Trigger**: Manual workflow_dispatch from feature branch

**Tags generated**:
- `ghcr.io/[repo]:feature-my-feature` ✅ (sanitized)
- `ghcr.io/[repo]:feature-my-feature-[short-sha]`

**No `:latest` tag** - `:latest` remains unchanged ✅

**Example**:
```
ghcr.io/yourusername/d365fo-client:feature-my-feature
ghcr.io/yourusername/d365fo-client:feature-my-feature-b4c5d6e
```

### Version Tags (`v1.2.3`)
**Trigger**: Push version tag or manual workflow_dispatch from tag

**Tags generated**:
- `ghcr.io/[repo]:1.2.3`
- `ghcr.io/[repo]:1.2`
- `ghcr.io/[repo]:1`
- `ghcr.io/[repo]:v1.2.3-[short-sha]`

**Example**:
```
ghcr.io/yourusername/d365fo-client:1.2.3
ghcr.io/yourusername/d365fo-client:1.2
ghcr.io/yourusername/d365fo-client:1
ghcr.io/yourusername/d365fo-client:v1.2.3-f8g9h0i
```

## How to Use On-Demand Builds

### Scenario 1: Testing a Feature Branch
1. Push your feature branch to GitHub
2. Go to **Actions → Docker Build and Push**
3. Click **Run workflow**
4. Select your feature branch from dropdown
5. Click **Run workflow**
6. Image will be pushed as `ghcr.io/[repo]:feature-branch-name`

### Scenario 2: Building Develop Branch
1. Go to **Actions → Docker Build and Push**
2. Click **Run workflow**
3. Select `develop` from dropdown
4. Click **Run workflow**
5. Image will be pushed as `ghcr.io/[repo]:develop`
6. **`:latest` tag is NOT affected** ✅

### Scenario 3: Pulling Branch-Specific Images

```bash
# Pull develop branch image
docker pull ghcr.io/yourusername/d365fo-client:develop

# Pull feature branch image
docker pull ghcr.io/yourusername/d365fo-client:feature-my-feature

# Pull latest (only from main)
docker pull ghcr.io/yourusername/d365fo-client:latest

# Pull specific SHA
docker pull ghcr.io/yourusername/d365fo-client:develop-a1b2c3d
```

## Workflow Configuration

### Key Features
- ✅ **Branch-based tagging**: Each branch gets its own tag
- ✅ **`:latest` protection**: Only applied to main branch
- ✅ **On-demand builds**: Manual trigger from any branch via `workflow_dispatch`
- ✅ **Semantic versioning**: Automatic version tag expansion
- ✅ **SHA tagging**: Every build tagged with git SHA for traceability

### Metadata Action Configuration
```yaml
tags: |
  # Latest only for main branch (explicit check)
  type=raw,value=latest,enable=${{ github.ref == 'refs/heads/main' }}
  # Version tags
  type=semver,pattern={{version}}
  type=semver,pattern={{major}}.{{minor}}
  type=semver,pattern={{major}}
  # Branch name
  type=ref,event=branch
  # PR number
  type=ref,event=pr
  # Git SHA
  type=sha,prefix={{branch}}-
```

**Important**: We use explicit `github.ref == 'refs/heads/main'` check instead of `{{is_default_branch}}` to ensure `:latest` is ONLY applied to the main branch, regardless of GitHub's default branch setting.

## Testing the Workflow

### Validation Checklist
- [ ] Push to `main` creates `:latest` tag
- [ ] Manual build from `develop` creates `:develop` tag (no `:latest`)
- [ ] Manual build from feature branch creates `:feature-name` tag (no `:latest`)
- [ ] Version tag `v1.0.0` creates `:1.0.0`, `:1.0`, `:1` tags
- [ ] All builds include SHA-based tags
- [ ] `:latest` tag is never overwritten by non-main builds

### Test Commands

```bash
# Test pulling different tags
docker pull ghcr.io/yourusername/d365fo-client:latest
docker pull ghcr.io/yourusername/d365fo-client:develop
docker pull ghcr.io/yourusername/d365fo-client:main

# Verify tag exists
docker manifest inspect ghcr.io/yourusername/d365fo-client:develop

# List all tags (requires GitHub CLI)
gh api /user/packages/container/d365fo-client/versions | jq -r '.[].metadata.container.tags[]'
```

## Troubleshooting

### Branch Name Sanitization
Docker tags don't support `/` or other special characters. The `docker/metadata-action` automatically sanitizes branch names:
- `feature/my-feature` → `feature-my-feature`
- `bugfix/issue-123` → `bugfix-issue-123`

### Permission Issues
Ensure the workflow has necessary permissions:
```yaml
permissions:
  contents: write
  packages: write
  id-token: write
```

### Manual Workflow Not Showing
If you don't see the "Run workflow" button:
1. Ensure you've pushed the workflow file to GitHub
2. Check that `workflow_dispatch` is in the triggers
3. Verify you have write access to the repository
