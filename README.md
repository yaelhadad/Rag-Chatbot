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
