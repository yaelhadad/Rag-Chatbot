# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a RAG (Retrieval-Augmented Generation) chatbot system with three distinct retrieval methods and a React frontend. The system demonstrates different RAG architectures for querying Frontegg documentation.

**Stack:**
- Backend: Python + Flask + LangChain + FAISS + Neo4j
- Frontend: React + Vite + Tailwind CSS
- LLM: OpenAI GPT-4o-mini (simple), GPT-4o (advanced)
- Vector Store: FAISS
- Graph Database: Neo4j (optional, for Method 3 only)

## Development Commands

### Backend

```bash
# Navigate to API directory
cd backend/rag_api

# Run the Flask server (port 5000)
python app.py

# The server runs with debug=True by default
```

### Frontend

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server (port 3000)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Environment Setup

The `.env` file must be in the **project root** (`Rag-Chatbot/`), not in subdirectories. Required structure:

```env
# Required for all methods
OPENAI_API_KEY=your_openai_api_key

# Required ONLY for Method 3 (Agentic RAG)
NEO4J_URI=neo4j+s://your_instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j
```

**Important:** Methods 1 and 2 work without Neo4j configuration. Method 3 requires Neo4j.

## Architecture Overview

### Core RAG Methods

The system implements three progressively sophisticated RAG strategies, each in its own module:

#### 1. Simple Vector RAG (`backend/rag_core/simple_vector.py`)
- **Strategy:** Direct FAISS vector search with MMR (Maximal Marginal Relevance)
- **Model:** `gpt-4o-mini` for speed and cost efficiency
- **Use Case:** Quick, straightforward questions
- **Retrieval:** Top K chunks directly from FAISS
- **Context Assembly:** Concatenates retrieved chunks with citation tags `[DocumentName - p.X]`

#### 2. Parent-Child RAG (`backend/rag_core/parent_child.py`)
- **Strategy:** Two-tier chunking for precision + context
- **Child Chunks:** 400 characters (precise retrieval via FAISS)
- **Parent Chunks:** 2000 characters (complete context for generation)
- **Model:** `gpt-4o` for better formatting compliance
- **Use Case:** Questions needing full context around a specific detail
- **Data Structures:**
  - `child_to_parent.pkl`: Maps child chunk IDs to parent chunk IDs
  - `parent_store.pkl`: Dictionary of parent chunks by ID
  - FAISS index: Searchable child chunks
- **Process:** Search child chunks → retrieve parent chunks → deduplicate by parent_id → generate answer

#### 3. Agentic RAG (`backend/rag_core/agentic_rag.py`)
- **Strategy:** Multi-tool agent with intelligent tool selection
- **Model:** `gpt-4o` for complex reasoning
- **Tools:**
  - `graph_search`: Neo4j knowledge graph (entity relationships)
  - `parent_child_search`: Documentation search (uses Method 2)
  - `query_entropy_analyzer`: Shannon entropy analysis for query complexity
  - `password_strength_analyzer`: Password security analysis
- **Current State:** Simplified implementation that delegates to parent-child search
- **Note:** Full agent implementation with tool selection is partially implemented but currently bypassed

### Backend Structure

```
backend/
├── rag_api/                    # Flask API layer
│   ├── app.py                  # App factory + CORS config
│   ├── config.py               # Configuration + env validation
│   └── routes/
│       ├── query_routes.py     # POST /api/query (main endpoint)
│       └── health_routes.py    # GET /api/health
└── rag_core/                   # RAG implementation
    ├── simple_vector.py        # Method 1
    ├── parent_child.py         # Method 2
    ├── agentic_rag.py          # Method 3
    └── utils/
        └── entropy_calculator.py  # Shannon entropy (O(n) complexity)
```

**Key Design Points:**
- RAG instances are initialized once at module load time (singleton pattern)
- Configuration loads from `Rag-Chatbot/.env` using `pathlib` resolution
- All methods set `OPENAI_API_KEY` in environment if not already set
- Neo4j driver uses lazy initialization (only connects when `_get_driver()` called)

### Frontend Architecture

```
frontend/src/
├── App.jsx                     # Root component + state management
├── components/
│   ├── ChatInterface.jsx       # Main chat layout
│   ├── MessageList.jsx         # Message container
│   ├── Message.jsx             # Individual message + sources
│   ├── Sources.jsx             # Source rendering (graph/parent-child/entropy)
│   ├── MethodSelector.jsx      # RAG method picker
│   └── InputArea.jsx           # Question input + submit
└── index.jsx                   # React root
```

**State Management:**
- Centralized in `App.jsx` (no Redux/Zustand)
- Messages array tracks full conversation
- Selected method (1, 2, or 3) determines backend RAG strategy
- API calls via fetch to `/api/query`

**Proxy Configuration:**
- Vite proxy forwards `/api/*` to `http://localhost:5000`
- Configured in `frontend/vite.config.js`

### Data Layer

FAISS vector stores are pre-built and stored in `data/faiss_stores/`:

```
data/faiss_stores/
├── simple_vector/              # Method 1 data
│   ├── index.faiss             # FAISS index
│   └── index.pkl               # LangChain metadata
└── parent_child/               # Method 2 data
    ├── index.faiss             # Child chunks (400 chars)
    ├── index.pkl               # Child metadata
    ├── parent_store.pkl        # Parent chunks (2000 chars)
    └── child_to_parent.pkl     # Mapping dict
```

**Important:** These are pre-built artifacts. There's no document ingestion pipeline in this repository.

## System Prompts and RAG Behavior

### Method 1 System Prompt
- Strict citation requirement: `[DocumentName - p.X]` for all claims
- Detects "complete implementation" requests and refuses if context insufficient
- Organized code formatting with section dividers

### Method 2 System Prompt
- Text-first approach (no code unless explicitly requested)
- Separates answerable vs. unanswerable parts
- Refuses relationship questions ("how does X connect to Y")
- Uses GPT-4o for better adherence to formatting rules

### Context Formatting
Both methods format context as:
```
[DocumentName - p.X]
<chunk content>

---

[DocumentName - p.Y]
<chunk content>
```

## API Endpoints

### POST /api/query
**Request:**
```json
{
  "method_id": 1,  // 1, 2, or 3
  "question": "How do I implement SSO?"
}
```

**Response:**
```json
{
  "success": true,
  "method_id": 1,
  "method_name": "Simple Vector RAG",
  "answer": "...",
  "sources": [
    {
      "type": "chunk",           // or "parent_chunk", "graph", "entropy_analysis"
      "content": "...",
      "metadata": {
        "title": "SSO Guide",
        "page": 5
      }
    }
  ],
  "source_count": 6,
  "execution_time_ms": 1234.56,
  "metadata": {
    "chunks_retrieved": 6,
    "model_used": "gpt-4o-mini"
  }
}
```

### GET /api/health
Returns available methods and system status.

## Common Development Patterns

### Adding a New RAG Method

1. Create module in `backend/rag_core/new_method.py`
2. Implement `query(question: str) -> dict` method
3. Return dict with keys: `answer`, `sources`, `metadata`
4. Register in `backend/rag_api/routes/query_routes.py`:
   ```python
   rag_methods = {
       1: SimpleVectorRAG(config),
       2: ParentChildRAG(config),
       4: NewMethodRAG(config)  # New method
   }
   METHOD_NAMES[4] = "New Method Name"
   ```
5. Update frontend `MethodSelector.jsx` to include method 4

### Modifying System Prompts

System prompts are defined as module-level constants at the top of each RAG file:
- `backend/rag_core/simple_vector.py` → `SYSTEM_PROMPT`
- `backend/rag_core/parent_child.py` → `SYSTEM_PROMPT`
- `backend/rag_core/agentic_rag.py` → Prompts in `_create_agent()`

### Debugging

**Backend Issues:**
- Check `.env` file exists in `Rag-Chatbot/` (NOT in `backend/`)
- Verify virtual environment is activated
- Check Flask console output for initialization errors
- Neo4j errors are expected if Method 3 is used without Neo4j config

**Frontend Issues:**
- Vite auto-selects next available port if 3000 is taken
- Check browser console for API errors
- API proxy requires backend to be running on port 5000

**Common Error:** "Module not found" when running `app.py`
- Cause: Running from wrong directory
- Solution: Must run from `backend/rag_api/`, not project root

## Configuration Details

### Model Selection (`backend/rag_api/config.py`)

```python
EMBED_MODEL = "text-embedding-3-small"    # Embeddings for all methods
CHAT_MODEL_SIMPLE = "gpt-4o-mini"         # Method 1
CHAT_MODEL_ADVANCED = "gpt-4o"            # Methods 2, 3
DEFAULT_TOP_K = 6                          # Retrieval count
DEFAULT_TEMPERATURE = 0.2                  # LLM temperature
```

### FAISS Paths
Paths are resolved relative to `BASE_DIR` (project root):
```python
METHOD_1_FAISS = "data/faiss_stores/simple_vector"
METHOD_2_FAISS = "data/faiss_stores/parent_child"
```

### Path Resolution
The config uses `Path(__file__).parent.parent.parent` to find the project root, which works when `config.py` is at `backend/rag_api/config.py`.

## Neo4j Knowledge Graph

**Schema (for Method 3):**
- Nodes represent entities (SSO, SAML, JWT, Magic Link, etc.)
- Relationships represent connections (USES, INCLUDES, REQUIRES, etc.)
- Query pattern: `MATCH (n)-[r]->(m) WHERE ... RETURN n.name, type(r), m.name`

**Tool Behavior:**
- `_graph_search()` extracts keywords from natural language queries
- Searches for entities containing those keywords
- Returns up to 15 relationships
- Example: "SSO" → "SSO -[USES]-> SAML", "SSO -[REQUIRES]-> JWT"

## Entropy Calculator (`backend/rag_core/utils/entropy_calculator.py`)

Implements Shannon entropy for two use cases:

1. **Query Complexity Analysis:**
   - Normalizes entropy to [0, 1]
   - Recommends tools based on entropy + keyword matching
   - O(n) time complexity (no API calls)

2. **Password Strength Analysis:**
   - Raw entropy in bits
   - Character diversity scoring
   - Strength ratings: weak/fair/medium/strong/very_strong
   - Returns recommendations for improvement

**Performance:** All calculations are local (no API/database calls), making them fast for real-time analysis.

## Testing Methodology

This project has no automated tests. Testing is done manually:

1. Start backend: `cd backend/rag_api && python app.py`
2. Start frontend: `cd frontend && npm run dev`
3. Test each method with various question types:
   - Simple: "What is SSO?"
   - Implementation: "How do I implement SAML?"
   - Relationship: "How does Magic Link connect to JWT?"
   - Password: "Is 'password123' secure?"

Check that:
- Citations appear in format `[DocumentName - p.X]`
- Sources match the answer content
- Execution time is reasonable (< 5s for most queries)
- Method 3 handles multi-part questions

## Frontend Source Rendering

The `Sources.jsx` component renders different UI based on source type:

- **`type: "chunk"`** (Method 1): Simple content box
- **`type: "parent_chunk"`** (Method 2): Shows parent_id in metadata
- **`type: "graph"`** (Method 3): Graph relationships formatting
- **`type: "entropy_analysis"`** (Method 3): Structured entropy display
- **`type: "password_analysis"`** (Method 3): Password strength card

This allows each RAG method to provide specialized source visualizations.

## Building the Knowledge Graph

### Graph Builder Script (`backend/rag_core/build_graph_from_chunks.py`)

This script builds the Neo4j knowledge graph required for Method 3's graph search functionality.

**Process:**
1. Loads all chunks from FAISS vector store
2. Uses GPT-4o-mini to extract entities and relationships from each chunk
3. Creates Neo4j nodes (entities) with comprehensive descriptions
4. Creates relationships between entities (SUPPORTS, USES_PROTOCOL, REQUIRES, etc.)

**Usage:**
```bash
cd backend/rag_core
python build_graph_from_chunks.py
```

**Interactive Prompts:**
- "Clear existing Neo4j graph?" - Wipes the database before building
- "Process all chunks or limit for testing?" - Can process subset for testing

**Important Configuration:**
- `STORE_DIR` (line 28): Points to FAISS location - default is `./frontegg_faiss_lc`
- You may need to update this to `../../data/faiss_stores/simple_vector` depending on where you run it from

**Graph Schema:**
- **Nodes:** Have `name`, `type`, `description`, and custom properties
- **Relationships:** Typed edges (SUPPORTS, INCLUDES, etc.) with descriptions
- **Descriptions:** Entities store comprehensive details to enable answering questions using only the graph

**Output:**
- Prints statistics: entity counts, relationship counts
- Provides Neo4j Browser visualization query
- Shows sample entities with descriptions

**Cost:** Uses GPT-4o-mini (~$0.10-0.20 for 150 chunks)

## Important Notes

1. **No Document Ingestion:** The FAISS stores are pre-built. To add new documents, you need a separate ingestion pipeline. The graph builder works with existing FAISS data.

2. **Neo4j is Optional:** Methods 1 and 2 work without Neo4j. Only Method 3 requires it, and even then, it's currently simplified to mostly use parent-child search.

3. **Agent Implementation:** Method 3's full agentic behavior (tool calling, multi-step reasoning) is partially implemented but currently bypassed in favor of a simplified approach.

4. **Path Sensitivity:** All relative paths assume execution from the correct directory (`backend/rag_api/` for backend).

5. **CORS:** Fully open CORS policy (`origins: "*"`). Tighten for production.

6. **API Key Security:** `.env` file should never be committed. It's in `.gitignore`.
