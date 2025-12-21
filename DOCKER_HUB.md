# Publishing to Docker Hub

This guide explains how to build and push your RAG Chatbot images to Docker Hub.

## Prerequisites

1. **Docker Hub Account**: Create one at [hub.docker.com](https://hub.docker.com)
2. **Docker Desktop**: Running and logged in

## Step 1: Login to Docker Hub

```bash
docker login
```

Enter your Docker Hub username and password when prompted.

## Step 2: Tag Your Images

### For Backend Image

```bash
# Replace 'yourusername' with your Docker Hub username
docker tag rag-chatbot-backend:latest yourusername/rag-chatbot-backend:latest

# Optional: Tag with version
docker tag rag-chatbot-backend:latest yourusername/rag-chatbot-backend:v1.0.0
```

### For Neo4j Image (if you want to publish it)

```bash
docker tag rag-chatbot-neo4j:latest yourusername/rag-chatbot-neo4j:latest
```

## Step 3: Push Images to Docker Hub

### Push Backend

```bash
docker push yourusername/rag-chatbot-backend:latest
docker push yourusername/rag-chatbot-backend:v1.0.0  # if you tagged a version
```

### Push Neo4j (Optional)

```bash
docker push yourusername/rag-chatbot-neo4j:latest
```

## Step 4: Update docker-compose.yml to Use Published Images

After pushing, you can update `docker-compose.yml` to use the published images:

```yaml
services:
  neo4j:
    image: yourusername/rag-chatbot-neo4j:latest
    # ... rest of config

  backend:
    image: yourusername/rag-chatbot-backend:latest
    # ... rest of config
```

## Automated Build Script

Create a `publish.sh` (or `publish.ps1` for Windows) script:

### For Linux/Mac (publish.sh)

```bash
#!/bin/bash

DOCKER_USERNAME="yourusername"
VERSION=${1:-latest}

echo "Building images..."
docker-compose build

echo "Tagging images..."
docker tag rag-chatbot-backend:latest ${DOCKER_USERNAME}/rag-chatbot-backend:${VERSION}
docker tag rag-chatbot-neo4j:latest ${DOCKER_USERNAME}/rag-chatbot-neo4j:${VERSION}

echo "Pushing to Docker Hub..."
docker push ${DOCKER_USERNAME}/rag-chatbot-backend:${VERSION}
docker push ${DOCKER_USERNAME}/rag-chatbot-neo4j:${VERSION}

echo "Done! Images pushed to Docker Hub"
```

### For Windows (publish.ps1)

A complete PowerShell script is provided in `publish.ps1`. Usage:

```powershell
# Publish with default 'latest' tag
.\publish.ps1

# Publish with specific version
.\publish.ps1 v1.0.0

# Publish with username specified
.\publish.ps1 -Version v1.0.0 -DockerUsername yourusername
```

The script automatically:
- Checks if Docker is running
- Builds the images
- Tags them correctly
- Logs in to Docker Hub (if needed)
- Pushes the images
- Shows Docker Hub URLs

## Quick Commands Reference

```bash
# 1. Login
docker login

# 2. Build images
docker-compose build

# 3. Tag backend
docker tag rag-chatbot-backend:latest yourusername/rag-chatbot-backend:latest

# 4. Tag Neo4j
docker tag rag-chatbot-neo4j:latest yourusername/rag-chatbot-neo4j:latest

# 5. Push both
docker push yourusername/rag-chatbot-backend:latest
docker push yourusername/rag-chatbot-neo4j:latest
```

## Using Published Images

Others can now pull and use your images:

```bash
# Pull your images
docker pull yourusername/rag-chatbot-backend:latest
docker pull yourusername/rag-chatbot-neo4j:latest

# Or use in docker-compose
docker-compose pull
docker-compose up -d
```

## Best Practices

1. **Use Version Tags**: Tag with version numbers (v1.0.0, v1.0.1, etc.)
2. **Keep `latest` Updated**: Always push to `latest` for the current stable version
3. **Use Semantic Versioning**: Follow MAJOR.MINOR.PATCH format
4. **Document Dependencies**: Update README with image names
5. **Security**: Never push images with secrets/API keys hardcoded

## Notes

- **Neo4j**: You might not need to publish Neo4j since it's already available as `neo4j:5.14-community`
- **Backend**: This is the main image you'll want to publish
- **Size**: Large images take time to push - be patient!
- **Public vs Private**: By default, images are public. Upgrade to Docker Hub Pro for private repos.

