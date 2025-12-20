import pickle
from pathlib import Path
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from typing import List

SYSTEM_PROMPT = """You are a technical assistant for Frontegg documentation.

CRITICAL RULES:
1. Answer ONLY using the provided context
2. Do NOT add information not in the context
3. For each factual claim, add citations [DocumentName - p.X]
4. Only show code if user explicitly asks for it (e.g., "implement", "code", "example", "how do I")

WHAT YOU CAN ANSWER:
- "What is X?" / "Explain X" → Text explanation only (NO code unless asked)
- "How do I implement X?" / "Show me the code" → Include code examples

WHAT YOU CANNOT ANSWER:
- "How does X connect to Y?" / "relate to" / "link to" → Say "I cannot answer this part"
- "Is this password secure/strong?" → Say "I cannot answer this part"

If question has MULTIPLE parts: Answer what you CAN, simply say "I cannot answer this part" for what you CANNOT.

Answer structure:
- Use markdown headers (## Section)
- Add citations [DocumentName - p.X] for claims
- Only include code if user asks for implementation"""


class ParentChildRAG:
    def __init__(self, config):
        # Set OpenAI API key in environment if not already set
        import os
        if config.OPENAI_API_KEY and not os.getenv("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
        
        self.embeddings = OpenAIEmbeddings(model=config.EMBED_MODEL)
        self.store_dir = Path(config.METHOD_2_FAISS)
        
        # Load FAISS vector store (child chunks - 400 chars)
        self.vstore = FAISS.load_local(
            str(self.store_dir),
            self.embeddings,
            allow_dangerous_deserialization=True
        )
        
        # Load parent store (parent chunks - 2000 chars)
        parent_store_path = self.store_dir / "parent_store.pkl"
        with open(parent_store_path, "rb") as f:
            self.parent_store = pickle.load(f)
        
        # Load child-to-parent mappings
        mappings_path = self.store_dir / "child_to_parent.pkl"
        with open(mappings_path, "rb") as f:
            self.child_to_parent = pickle.load(f)
        
        # Using ADVANCED model for better formatting compliance
        self.llm = ChatOpenAI(model=config.CHAT_MODEL_ADVANCED, temperature=0.2)
        self.config = config
    
    def query(self, question: str, top_k: int = 6) -> dict:
        # STEP 1: Retrieve parent documents using child-based search
        parent_docs = self._retrieve_parent_docs(question, top_k)
        
        # STEP 2: Format context from parent chunks
        context = self._format_context(parent_docs)
        
        # STEP 3: Generate answer with complete parent context
        answer = self._generate_answer(question, context)
        
        # Return structured data
        return {
            "answer": answer,
            "sources": [
                {
                    "type": "parent_chunk",
                    "content": doc.page_content,
                    "metadata": {
                        "title": doc.metadata.get("title", "Unknown"),
                        "page": doc.metadata.get("page", "?"),
                        "parent_id": doc.metadata.get("parent_id", "unknown")
                    }
                }
                for doc in parent_docs
            ],
            "metadata": {
                "parent_chunks_retrieved": len(parent_docs),
                "model_used": self.llm.model_name,
                "strategy": "parent-child (child=400, parent=2000)"
            }
        }
    
    def _retrieve_parent_docs(self, question: str, k: int) -> List[Document]:
        """Search child chunks, return parent chunks"""
        # Search child chunks with MMR (precise retrieval)
        child_docs = self.vstore.max_marginal_relevance_search(
            question, k=k, fetch_k=k * 4, lambda_mult=0.5
        )
        
        # Map to parent chunks (complete context)
        parent_ids_seen = set()
        parent_docs = []
        
        for child_doc in child_docs:
            parent_id = child_doc.metadata.get("parent_id")
            if parent_id and parent_id not in parent_ids_seen:
                parent_ids_seen.add(parent_id)
                parent_doc = self.parent_store.get(parent_id)
                if parent_doc:
                    parent_docs.append(parent_doc)
        
        return parent_docs
    
    def _format_context(self, docs: List[Document]) -> str:
        """Format parent documents as context"""
        blocks = []
        for i, doc in enumerate(docs, start=1):
            meta = doc.metadata or {}
            doc_title = meta.get("title", "Unknown")
            page = meta.get("page", "?")
            tag = f"[{doc_title} - p.{page}]"
            blocks.append(f"{tag}\n{doc.page_content.strip()}")
        return "\n\n---\n\n".join(blocks)
    
    def _generate_answer(self, question: str, context: str) -> str:
        """Generate answer using LLM with parent context"""
        user_prompt = f"""Question: {question}

Context:
{context}

Answer the parts you CAN from the documentation context above.

IMPORTANT: Only include code if the question explicitly asks for implementation, code, or examples.
- "What is X?" → Text explanation only, NO code
- "How do I implement X?" / "Show code" → Include code

For parts you cannot answer:
- "How does X connect to Y?" → Simply say "I cannot answer this part"
- "Is password secure?" → Simply say "I cannot answer this part"

Provide:
- ## Overview (brief text summary)
- ## Answer (text explanation from documentation, code ONLY if asked)
- ## What I Cannot Answer (just list the parts)
- ## Key Points (bullets with citations [DocName - p.X])"""
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        response = self.llm.invoke(messages)
        return response.content

