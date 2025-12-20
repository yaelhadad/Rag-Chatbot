# RAG API

Flask REST API for the RAG Chatbot system.

## Installation

```bash
cd chatbot/backend/rag_api
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the `chatbot/` directory:

```env
OPENAI_API_KEY=your_openai_api_key

# For Method 3 (Agentic RAG) only:
NEO4J_URI=neo4j+s://your_instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j
```

## Running

```bash
python app.py
```

The API will start on `http://localhost:5000`

## Endpoints

### Health Check
```
GET /api/health
```

### Get Methods
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

## Methods

1. **Simple Vector RAG** - Fast FAISS vector search
2. **Parent-Child RAG** - Precise child chunks + complete parent context
3. **Agentic RAG** - Multi-tool agent with graph search, parent-child, and entropy analysis

