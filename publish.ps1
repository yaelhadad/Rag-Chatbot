# PowerShell script to build and push images to Docker Hub
# Usage: .\publish.ps1 [version]
# Example: .\publish.ps1 v1.0.0

param(
    [string]$Version = "latest",
    [string]$DockerUsername = ""
)

# Check if Docker is running
Write-Host "Checking Docker..." -ForegroundColor Cyan
try {
    docker ps | Out-Null
    Write-Host "✓ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Get Docker Hub username
if ([string]::IsNullOrEmpty($DockerUsername)) {
    $DockerUsername = Read-Host "Enter your Docker Hub username"
}

if ([string]::IsNullOrEmpty($DockerUsername)) {
    Write-Host "✗ Docker Hub username is required" -ForegroundColor Red
    exit 1
}

Write-Host "`nBuilding images..." -ForegroundColor Cyan
docker-compose build

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Build failed" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Images built successfully" -ForegroundColor Green

# Get image names from docker-compose
Write-Host "`nTagging images..." -ForegroundColor Cyan

# Backend image
$backendImage = "rag-chatbot-backend"
$backendTag = "${DockerUsername}/rag-chatbot-backend:${Version}"
docker tag "${backendImage}:latest" $backendTag
Write-Host "✓ Tagged: $backendTag" -ForegroundColor Green

# Neo4j image (optional - you might skip this since Neo4j official image exists)
$neo4jImage = "rag-chatbot-neo4j"
$neo4jTag = "${DockerUsername}/rag-chatbot-neo4j:${Version}"
docker tag "${neo4jImage}:latest" $neo4jTag
Write-Host "✓ Tagged: $neo4jTag" -ForegroundColor Green

# Check if logged in to Docker Hub
Write-Host "`nChecking Docker Hub login..." -ForegroundColor Cyan
try {
    docker info | Select-String "Username" | Out-Null
    Write-Host "✓ Already logged in to Docker Hub" -ForegroundColor Green
} catch {
    Write-Host "Please login to Docker Hub:" -ForegroundColor Yellow
    docker login
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Login failed" -ForegroundColor Red
        exit 1
    }
}

# Push images
Write-Host "`nPushing images to Docker Hub..." -ForegroundColor Cyan
Write-Host "This may take a while depending on your internet connection..." -ForegroundColor Yellow

docker push $backendTag
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to push backend image" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Pushed: $backendTag" -ForegroundColor Green

# Ask if user wants to push Neo4j image
$pushNeo4j = Read-Host "`nPush Neo4j image? (y/n)"
if ($pushNeo4j -eq "y" -or $pushNeo4j -eq "Y") {
    docker push $neo4jTag
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Failed to push Neo4j image" -ForegroundColor Red
    } else {
        Write-Host "✓ Pushed: $neo4jTag" -ForegroundColor Green
    }
}

Write-Host "`n✓ Done! Images published to Docker Hub" -ForegroundColor Green
Write-Host "`nYour images are available at:" -ForegroundColor Cyan
Write-Host "  - https://hub.docker.com/r/${DockerUsername}/rag-chatbot-backend" -ForegroundColor White
if ($pushNeo4j -eq "y" -or $pushNeo4j -eq "Y") {
    Write-Host "  - https://hub.docker.com/r/${DockerUsername}/rag-chatbot-neo4j" -ForegroundColor White
}

