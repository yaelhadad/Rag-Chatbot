from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from pathlib import Path

SYSTEM_PROMPT = """You are a technical assistant for Frontegg documentation.

CRITICAL RULES:
1. Answer ONLY using the provided context. Do NOT add information not in the context.
2. If the answer is not supported by the context, say "I don't know" or "This information is not in the provided context".
3. For EACH factual claim, add an inline citation in the format [DocumentName - p.X].
4. If the user asks for a COMPLETE implementation (e.g., "complete", "full", "end-to-end", "required function", "all the logic", "including errors"):
   - Only answer with code if the context contains the full runnable code for that request.
   - Otherwise, respond: "I don't have complete information in the provided context to answer this question fully."

Answer structure:
- Use markdown headers (## Section)
- Provide complete, runnable code examples only when the context includes the full implementation.
- Add citations [DocumentName - p.X] for claims

Code formatting:
- Use section dividers: // ============ SECTION NAME ============
- Add blank lines between sections and steps
- Organize: IMPORTS → CONFIG → LOGIC → ROUTES → INIT

Example structure:
```javascript
// ============================================
// IMPORTS
// ============================================
const express = require('express');
const jwt = require('jsonwebtoken');
```"""


class SimpleVectorRAG:
    def __init__(self, config):
        # Set OpenAI API key in environment if not already set
        import os
        if config.OPENAI_API_KEY and not os.getenv("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
        
        self.embeddings = OpenAIEmbeddings(model=config.EMBED_MODEL)
        self.vstore = FAISS.load_local(
            config.METHOD_1_FAISS,
            self.embeddings,
            allow_dangerous_deserialization=True
        )
        self.llm = ChatOpenAI(model=config.CHAT_MODEL_SIMPLE, temperature=config.DEFAULT_TEMPERATURE)
        self.config = config

    def query(self, question: str, top_k: int = 6) -> dict:
        # MMR search
        docs = self.vstore.max_marginal_relevance_search(
            question, k=top_k, fetch_k=20, lambda_mult=0.5
        )

        # Format context and messages
        context = self._format_context(docs)
        messages = self._build_messages(question, context)

        # Get LLM response
        response = self.llm.invoke(messages)

        # Return structured data
        return {
            "answer": response.content,
            "sources": [
                {
                    "type": "chunk",
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in docs
            ],
            "metadata": {
                "chunks_retrieved": len(docs),
                "model_used": self.config.CHAT_MODEL_SIMPLE
            }
        }

    def _format_context(self, docs) -> str:
        blocks = []
        for i, d in enumerate(docs, start=1):
            meta = d.metadata or {}
            # Get document title or filename
            doc_title = meta.get("title", "Unknown Document")
            page = meta.get("page", "?")
            tag = f"[{doc_title} - p.{page}]"
            blocks.append(f"{tag}\n{d.page_content.strip()}")
        return "\n\n".join(blocks)

    def _build_messages(self, question: str, context: str):
        user_prompt = f"""Question: {question}

Context:
{context}

Answer ONLY from the context above.

If the question requests a COMPLETE implementation/function/end-to-end code and the context does NOT contain the full runnable code, respond exactly with:
I don't have complete information in the provided context to answer this question fully.

Otherwise, provide:
- ## Overview
- ## Answer
- ## Key Points"""
        
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

