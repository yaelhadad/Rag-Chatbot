# Neo4j Service for RAG Chatbot

Standalone Neo4j service configuration for the RAG Chatbot project.

## Quick Start

### Using Docker Compose (Recommended)

1. **Set environment variables** (create `.env` file or export):
```bash
export NEO4J_USERNAME=neo4j
export NEO4J_PASSWORD=your_secure_password
```

Or create a `.env` file:
```env
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_secure_password
```

2. **Start Neo4j:**
```bash
docker-compose up -d
```

3. **Access Neo4j Browser:**
- Open `http://localhost:7474` in your browser
- Login with your credentials

4. **Stop Neo4j:**
```bash
docker-compose down
```

### Using Docker Directly

1. **Build the image:**
```bash
docker build -t rag-chatbot-neo4j:latest .
```

2. **Run the container:**
```bash
docker run -d \
  --name rag-chatbot-neo4j \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -e NEO4J_PLUGINS=["apoc"] \
  -v neo4j_data:/data \
  -v neo4j_logs:/logs \
  rag-chatbot-neo4j:latest
```

## Configuration

### Environment Variables

- `NEO4J_USERNAME` - Neo4j username (default: `neo4j`)
- `NEO4J_PASSWORD` - Neo4j password (default: `password`)
- `NEO4J_PLUGINS` - Plugins to enable (default: `["apoc"]`)

### Memory Settings

Default memory configuration:
- Heap initial: 512MB
- Heap max: 2GB
- Page cache: 1GB

To customize, modify environment variables in `docker-compose.yml`:
```yaml
- NEO4J_dbms_memory_heap_initial__size=1G
- NEO4J_dbms_memory_heap_max__size=4G
- NEO4J_dbms_memory_pagecache_size=2G
```

## Volumes

- `neo4j_data` - Database data (persistent)
- `neo4j_logs` - Log files
- `neo4j_import` - Import directory for CSV/JSON files
- `neo4j_plugins` - Plugin storage
- `neo4j_conf` - Configuration files

## Connection Details

- **Bolt URI:** `bolt://localhost:7687`
- **HTTP URI:** `http://localhost:7474`
- **Browser:** `http://localhost:7474`

## Integration with Main Project

To use this Neo4j service with the main RAG Chatbot:

1. **Start Neo4j from this directory:**
```bash
cd neo4j
docker-compose up -d
```

2. **Update main project `.env`:**
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
```

3. **Start the main backend** (it will connect to this Neo4j instance)

## Troubleshooting

### Check Neo4j Status
```bash
docker-compose ps
docker-compose logs neo4j
```

### Reset Neo4j (Delete All Data)
```bash
docker-compose down -v
docker-compose up -d
```

### Access Neo4j Shell
```bash
docker exec -it rag-chatbot-neo4j cypher-shell -u neo4j -p your_password
```

### Import Data
Place CSV/JSON files in the `neo4j_import` volume, then use Cypher:
```cypher
LOAD CSV FROM 'file:///import/yourfile.csv' AS row
CREATE (n:Node {property: row[0]})
```

