# RAG Chatbot

A comprehensive RAG (Retrieval-Augmented Generation) chatbot system with multiple retrieval methods and a modern React frontend.

## Features

- **3 RAG Methods**: Simple Vector, Parent-Child, and Agentic RAG
- **Modern Frontend**: React-based UI with real-time chat interface
- **RESTful API**: Flask backend with CORS support
- **Multiple Data Sources**: FAISS vector stores, Neo4j knowledge graph
- **Source Attribution**: Detailed source display with citations

## Project Structure

```
Rag-Chatbot/
├── backend/
│   ├── rag_api/          # Flask API server
│   └── rag_core/          # RAG implementation logic
├── frontend/              # React frontend application
├── data/                  # FAISS vector stores
└── requirements.txt       # Python dependencies
```

## Prerequisites

- Python 3.8+ (with virtual environment)
- Node.js 16+ and npm
- OpenAI API key
- (Optional) Neo4j instance for Method 3

## Installation

### Backend Setup

1. **Navigate to project root:**
```bash
cd Rag-Chatbot
```

2. **Create and activate virtual environment:**
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

3. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

### Frontend Setup

1. **Navigate to frontend directory:**
```bash
cd frontend
```

2. **Install Node.js dependencies:**
```bash
npm install
```

## Configuration

Create a `.env` file in the `Rag-Chatbot/` directory:

```env
# Required
OPENAI_API_KEY=your_openai_api_key

# Optional - Only needed for Method 3 (Agentic RAG)
NEO4J_URI=neo4j+s://your_instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j
```

**Note:** The app will start without Neo4j configuration, but Method 3 will only work if Neo4j is properly configured.

## Running the Application

### Start Backend (Terminal 1)

```bash
cd Rag-Chatbot/backend/rag_api
python app.py
```

The API will start on `http://localhost:5000`

### Start Frontend (Terminal 2)

```bash
cd Rag-Chatbot/frontend
npm run dev
```

The frontend will start on `http://localhost:3000` (or next available port)

### Access the Application

Open your browser and navigate to the frontend URL (typically `http://localhost:3000`)

## API Endpoints

### Health Check
```
GET /api/health
```

### Get Available Methods
```
GET /api/methods
```

### Query
```
POST /api/query
Content-Type: application/json

{
  "method_id": 1,  // 1, 2, or 3
  "question": "Your question here"
}
```

**Response:**
```json
{
  "success": true,
  "method_id": 1,
  "method_name": "Simple Vector RAG",
  "answer": "...",
  "sources": [...],
  "source_count": 6,
  "execution_time_ms": 1234.56,
  "metadata": {...}
}
```

## RAG Methods

### 1. Simple Vector RAG
- **Fast FAISS vector search** with MMR (Maximal Marginal Relevance)
- Best for: Quick, straightforward questions
- Retrieves: Top K most relevant document chunks

### 2. Parent-Child RAG
- **Precise child chunks** (400 chars) for retrieval
- **Complete parent context** (2000 chars) for generation
- Best for: Questions needing full context
- Retrieves: Child chunks, returns parent chunks with complete context

### 3. Agentic RAG
- **Multi-tool agent** with intelligent tool selection
- Tools:
  - `graph_search`: Neo4j knowledge graph for relationships
  - `parent_child_search`: Documentation search
  - `query_entropy_analyzer`: Query complexity analysis
  - `password_strength_analyzer`: Password security analysis
- Best for: Complex, multi-part questions
- Automatically selects and combines multiple tools

## Dependencies

### Backend (Python)
- `flask>=3.0.0` - Web framework
- `langchain>=0.1.0` - LLM framework
- `langchain-openai>=0.0.5` - OpenAI integration
- `langchain-community>=0.0.20` - Community integrations
- `langchain-core>=0.1.0` - Core LangChain functionality
- `langgraph>=0.2.0` - Agent execution engine
- `faiss-cpu>=1.7.4` - Vector similarity search
- `neo4j>=5.14.0` - Graph database (optional)
- `openai>=1.12.0` - OpenAI API client

### Frontend (Node.js)
- React - UI framework
- Vite - Build tool and dev server
- Tailwind CSS - Styling

## Troubleshooting


### Backend Issues

**Import Errors:**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Verify virtual environment is activated

**Neo4j Connection Errors:**
- Method 3 requires Neo4j configuration in `.env`
- The app will start without Neo4j, but Method 3 will fail when used
- Check Neo4j URI format: `neo4j+s://` or `bolt://`

**Module Not Found:**
- Ensure you're running from the correct directory
- Check Python path and virtual environment

### Frontend Issues

**Port Already in Use:**
- Vite will automatically use the next available port
- Check the terminal output for the actual URL

**API Connection Errors:**
- Ensure backend is running on `http://localhost:5000`
- Check CORS configuration in backend
- Verify API endpoints are accessible

## Development

### Backend Development
```bash
cd backend/rag_api
python app.py  # Runs with debug=True
```

### Frontend Development
```bash
cd frontend
npm run dev    # Hot reload enabled
```

## Docker Deployment

### Building and Running with Docker

#### Option 1: Docker Compose (Recommended)

1. **Create a `.env` file** in the project root:
```env
OPENAI_API_KEY=your_openai_api_key

# Neo4j Configuration (Optional - defaults provided)
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_secure_password
NEO4J_DATABASE=neo4j
```

**Note:** When using Docker Compose, `NEO4J_URI` is automatically set to `bolt://neo4j:7687` to connect to the Neo4j container. You don't need to set it manually.

2. **Build and run:**
```bash
docker-compose up -d
```

This will start:
- **Neo4j** service on ports `7474` (HTTP) and `7687` (Bolt)
- **Backend** service on port `5000` (waits for Neo4j to be healthy)

3. **View logs:**
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f neo4j
```

4. **Access Neo4j Browser:**
- Open `http://localhost:7474` in your browser
- Login with your Neo4j credentials from `.env`

5. **Stop services:**
```bash
docker-compose down

# To also remove volumes (deletes Neo4j data):
docker-compose down -v
```

#### Option 2: Docker Build and Run

1. **Build the image:**
```bash
docker build -t rag-chatbot:latest .
```

2. **Run the container:**
```bash
docker run -d \
  --name rag-chatbot \
  -p 5000:5000 \
  -e OPENAI_API_KEY=your_openai_api_key \
  -e NEO4J_URI=neo4j+s://your_instance.databases.neo4j.io \
  -e NEO4J_USERNAME=neo4j \
  -e NEO4J_PASSWORD=your_password \
  -v $(pwd)/data:/app/data \
  rag-chatbot:latest
```

3. **View logs:**
```bash
docker logs -f rag-chatbot
```

4. **Stop and remove:**
```bash
docker stop rag-chatbot
docker rm rag-chatbot
```

### Docker Features

- **Multi-stage build** for optimized image size
- **Health checks** to monitor container status
- **Volume mounting** for persistent FAISS data stores and Neo4j data
- **Service dependencies** - Backend waits for Neo4j to be healthy before starting
- **Neo4j integration** - Full Neo4j database included in Docker Compose
- **Environment variable** support for configuration
- **Production-ready** with proper error handling

### Neo4j Service Details

The Neo4j service includes:
- **Neo4j 5.14 Community Edition** with APOC plugins
- **Persistent volumes** for data, logs, and imports
- **Health checks** to ensure database is ready
- **Automatic connection** - Backend automatically connects to Neo4j container
- **Web interface** available at `http://localhost:7474`

### Frontend Docker (Optional)

To containerize the frontend:

1. **Build frontend image:**
```bash
cd frontend
docker build -t rag-chatbot-frontend:latest .
```

2. **Run frontend:**
```bash
docker run -d \
  --name rag-chatbot-frontend \
  -p 3000:80 \
  rag-chatbot-frontend:latest
```

Or use the `docker-compose.yml` file and uncomment the frontend service.

## Publishing to Docker Hub

To publish your images to Docker Hub:

1. **Login to Docker Hub:**
```bash
docker login
```

2. **Build and tag images:**
```bash
# Build images
docker-compose build

# Tag backend image (replace 'yourusername' with your Docker Hub username)
docker tag rag-chatbot-backend:latest yourusername/rag-chatbot-backend:latest

# Tag Neo4j image (optional)
docker tag rag-chatbot-neo4j:latest yourusername/rag-chatbot-neo4j:latest
```

3. **Push to Docker Hub:**
```bash
docker push yourusername/rag-chatbot-backend:latest
docker push yourusername/rag-chatbot-neo4j:latest
```

See `DOCKER_HUB.md` for detailed instructions and automation scripts.

## Using Published Images (For End Users)

If you want to use the published Docker images instead of building locally:

### Quick Start with Published Images

1. **Create a `.env` file:**
```env
OPENAI_API_KEY=your_openai_api_key
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_secure_password
```

2. **Use the pull-compose file (replace 'yourusername' with the Docker Hub username):**
```bash
# Edit docker-compose.pull.yml and replace 'yourusername' with actual username
# Then run:
docker-compose -f docker-compose.pull.yml pull
docker-compose -f docker-compose.pull.yml up -d
```

3. **Or use docker-compose.yml with image names:**
   - Edit `docker-compose.yml` and change `build:` sections to `image: yourusername/rag-chatbot-*:latest`
   - Then run: `docker-compose pull && docker-compose up -d`

See `USER_GUIDE.md` for complete instructions on using published images.
