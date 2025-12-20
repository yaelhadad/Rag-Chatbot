import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from Rag-Chatbot/ directory
BASE_DIR = Path(__file__).parent.parent.parent  # Rag-Chatbot/
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

class Config:
    def __init__(self):
        # Paths
        self.BASE_DIR = BASE_DIR
        self.DATA_DIR = BASE_DIR / "data"
        
        # API Keys
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        
        # Validate required configuration
        if not self.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is not set. Please create a .env file in the Rag-Chatbot/ "
                "directory with:\n"
                "OPENAI_API_KEY=your_openai_api_key\n\n"
                f"Expected .env file location: {env_path}"
            )
        
        # Neo4j (for Method 3 - Agentic RAG only)
        self.NEO4J_URI = os.getenv("NEO4J_URI")
        self.NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
        self.NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
        self.NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")
        
        # FAISS Paths
        self.METHOD_1_FAISS = str(self.DATA_DIR / "faiss_stores" / "simple_vector")
        self.METHOD_2_FAISS = str(self.DATA_DIR / "faiss_stores" / "parent_child")
        
        # Model Configuration
        self.EMBED_MODEL = "text-embedding-3-small"
        self.CHAT_MODEL_SIMPLE = "gpt-4o-mini"
        self.CHAT_MODEL_ADVANCED = "gpt-4o"
        
        # RAG Parameters
        self.DEFAULT_TOP_K = 6
        self.DEFAULT_TEMPERATURE = 0.2

