# User Guide - Using Published Docker Images

This guide explains how to use the published RAG Chatbot images from Docker Hub.

## Prerequisites

- Docker Desktop installed and running
- Docker Hub account (optional, only needed for private images)
- OpenAI API key

## Quick Start

### Option 1: Using Docker Compose (Recommended)

1. **Create a `docker-compose.yml` file:**

```yaml
services:
  neo4j:
    image: yourusername/rag-chatbot-neo4j:latest
    container_name: rag-chatbot-neo4j
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/password
      - NEO4J_PLUGINS=["apoc"]
      - NEO4J_dbms_security_procedures_unrestricted=apoc.*
      - NEO4J_dbms_security_procedures_allowlist=apoc.*
      - NEO4J_apoc_export_file_enabled=true
      - NEO4J_apoc_import_file_enabled=true
      - NEO4J_apoc_import_file_use__neo4j__config=true
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
      - neo4j_import:/var/lib/neo4j/import
      - neo4j_plugins:/plugins
    restart: unless-stopped

  backend:
    image: yourusername/rag-chatbot-backend:latest
    container_name: rag-chatbot-backend
    ports:
      - "5000:5000"
    environment:
      - OPENAI_API_KEY=your_openai_api_key
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USERNAME=neo4j
      - NEO4J_PASSWORD=password
      - NEO4J_DATABASE=neo4j
    volumes:
      - ./data:/app/data
    depends_on:
      neo4j:
        condition: service_healthy
    restart: unless-stopped

volumes:
  neo4j_data:
  neo4j_logs:
  neo4j_import:
  neo4j_plugins:
```

2. **Create a `.env` file (optional, for easier configuration):**

```env
OPENAI_API_KEY=your_openai_api_key
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_secure_password
```

3. **Pull and start services:**

```bash
# Pull images from Docker Hub
docker-compose pull

# Start services
docker-compose up -d

# View logs
docker-compose logs -f
```

### Option 2: Using Docker Commands Directly

#### Start Neo4j

```bash
docker run -d \
  --name rag-chatbot-neo4j \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -e NEO4J_PLUGINS=["apoc"] \
  -v neo4j_data:/data \
  -v neo4j_logs:/logs \
  yourusername/rag-chatbot-neo4j:latest
```

#### Start Backend

```bash
docker run -d \
  --name rag-chatbot-backend \
  -p 5000:5000 \
  -e OPENAI_API_KEY=your_openai_api_key \
  -e NEO4J_URI=bolt://localhost:7687 \
  -e NEO4J_USERNAME=neo4j \
  -e NEO4J_PASSWORD=password \
  -v $(pwd)/data:/app/data \
  --link rag-chatbot-neo4j:neo4j \
  yourusername/rag-chatbot-backend:latest
```

## Configuration

### Required Environment Variables

- `OPENAI_API_KEY` - Your OpenAI API key (required)

### Optional Environment Variables

- `NEO4J_USERNAME` - Neo4j username (default: `neo4j`)
- `NEO4J_PASSWORD` - Neo4j password (default: `password`)
- `NEO4J_DATABASE` - Neo4j database name (default: `neo4j`)

### Data Directory

The backend needs access to FAISS vector stores. You have two options:

1. **Mount local data directory:**
```bash
-v /path/to/your/data:/app/data
```

2. **Use default data** (if included in image):
   - The image may include pre-built FAISS stores
   - If not, you'll need to provide them

## Accessing the Services

### Backend API
- **URL:** `http://localhost:5000`
- **Health Check:** `http://localhost:5000/api/health`
- **API Docs:** `http://localhost:5000/`

### Neo4j Browser
- **URL:** `http://localhost:7474`
- **Login:** Use your Neo4j credentials

## Example Usage

### Test the API

```bash
# Health check
curl http://localhost:5000/api/health

# Query example
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "method_id": 1,
    "question": "What is authentication?"
  }'
```

### Using with Frontend

1. **Start backend and Neo4j:**
```bash
docker-compose up -d
```

2. **Run frontend locally:**
```bash
cd frontend
npm install
npm run dev
```

3. **Access frontend:** `http://localhost:3000`

## Troubleshooting

### Images Not Found

If you get "image not found" error:
```bash
# Pull the images explicitly
docker pull yourusername/rag-chatbot-backend:latest
docker pull yourusername/rag-chatbot-neo4j:latest
```

### Connection Issues

**Backend can't connect to Neo4j:**
- Ensure Neo4j container is running: `docker ps`
- Check Neo4j is healthy: `docker logs rag-chatbot-neo4j`
- Verify `NEO4J_URI=bolt://neo4j:7687` (use service name, not localhost)

**Port conflicts:**
- Change ports in docker-compose.yml if 5000, 7474, or 7687 are in use

### Missing Data Files

If you get errors about missing FAISS stores:
- Ensure the `data/` directory is mounted correctly
- Check that FAISS store files exist in `data/faiss_stores/`
- Contact the image maintainer for data files

## Updating Images

To get the latest version:

```bash
# Pull latest images
docker-compose pull

# Restart services
docker-compose up -d
```

## Stopping Services

```bash
# Stop services
docker-compose down

# Stop and remove volumes (deletes Neo4j data)
docker-compose down -v
```

## Support

For issues or questions:
- Check the main README.md
- Review Docker logs: `docker-compose logs`
- Contact the repository maintainer

