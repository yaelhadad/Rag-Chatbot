import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from chatbot/ directory
BASE_DIR = Path(__file__).parent.parent.parent  # chatbot/
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

class Config:
    # Paths
    BASE_DIR = BASE_DIR
    DATA_DIR = BASE_DIR / "data"
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Neo4j (for Method 3 - Agentic RAG only)
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
    NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")
    
    # FAISS Paths
    METHOD_1_FAISS = str(DATA_DIR / "faiss_stores" / "simple_vector")
    METHOD_2_FAISS = str(DATA_DIR / "faiss_stores" / "parent_child")
    
    # Model Configuration
    EMBED_MODEL = "text-embedding-3-small"
    CHAT_MODEL_SIMPLE = "gpt-4o-mini"
    CHAT_MODEL_ADVANCED = "gpt-4o"
    
    # RAG Parameters
    DEFAULT_TOP_K = 6
    DEFAULT_TEMPERATURE = 0.2

