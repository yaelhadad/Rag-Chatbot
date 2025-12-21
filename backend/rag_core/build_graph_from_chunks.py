"""
Build Neo4j Knowledge Graph from Existing FAISS Chunks
=======================================================
Reads chunks from FAISS database and builds a comprehensive knowledge graph
that enables graph-only retrieval with detailed, comprehensive answers.

Strategy:
1. Load all chunks from FAISS
2. Group chunks by document/page for context
3. Use LLM to extract entities and relationships with RICH details
4. Build hierarchical graph structure in Neo4j
5. Each entity stores comprehensive information to enable full answers
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Any
import json

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from neo4j import GraphDatabase

load_dotenv()

# FAISS Configuration
STORE_DIR = Path("./frontegg_faiss_lc")
EMBED_MODEL = "text-embedding-3-small"

# Neo4j Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

# LLM for extraction
EXTRACTION_MODEL = "gpt-4o-mini"

EXTRACTION_PROMPT = """You are a knowledge graph extraction expert. Extract entities and relationships from the following text.

CRITICAL: For each entity, include COMPREHENSIVE, DETAILED information in the description field.
The description should contain ALL important details about the entity so that someone can answer questions using ONLY the graph.

Extract:
1. **Entities**: Important concepts, methods, features, protocols, etc.
   - For each entity, provide:
     - name: Clear, specific name
     - type: Category (AuthMethod, SecurityFeature, Protocol, Platform, Risk, Control, etc.)
     - description: COMPREHENSIVE description with ALL relevant details (implementation, use cases, security, benefits, requirements, etc.)
     - properties: Any specific attributes (complexity, security_level, etc.)

2. **Relationships**: How entities relate to each other
   - Format: (source_entity) -[RELATIONSHIP_TYPE]-> (target_entity)
   - Relationship types: SUPPORTS, INCLUDES, USES_PROTOCOL, REQUIRES, PROTECTS_AGAINST, ENABLES, etc.

Text to analyze:
{text}

Return a JSON object with this structure:
{{
  "entities": [
    {{
      "name": "Entity Name",
      "type": "EntityType",
      "description": "Comprehensive description with ALL details including: what it is, how it works, use cases, security considerations, implementation details, benefits, limitations, requirements, best practices, etc.",
      "properties": {{"key": "value"}}
    }}
  ],
  "relationships": [
    {{
      "source": "Source Entity Name",
      "target": "Target Entity Name",
      "type": "RELATIONSHIP_TYPE",
      "description": "Why this relationship exists"
    }}
  ]
}}

IMPORTANT: Make descriptions extremely detailed and comprehensive. Include technical details, implementation guidance, security considerations, and use cases."""


class GraphBuilder:
    """Builds Neo4j graph from FAISS chunks"""

    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        self.llm = ChatOpenAI(model=EXTRACTION_MODEL, temperature=0)

    def close(self):
        self.driver.close()

    def clear_graph(self):
        """Clear existing graph"""
        with self.driver.session(database=NEO4J_DATABASE) as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("🗑️  Graph cleared")

    def load_chunks_from_faiss(self) -> List[Dict[str, Any]]:
        """Load all chunks from FAISS database"""
        if not STORE_DIR.exists():
            raise SystemExit(f"❌ FAISS store not found at {STORE_DIR}")

        print("📚 Loading chunks from FAISS...")
        embeddings = OpenAIEmbeddings(model=EMBED_MODEL)
        vstore = FAISS.load_local(str(STORE_DIR), embeddings, allow_dangerous_deserialization=True)

        # Get all documents
        all_docs = vstore.docstore._dict

        chunks = []
        for doc_id, doc in all_docs.items():
            meta = doc.metadata or {}
            chunks.append({
                "id": doc_id,
                "text": doc.page_content,
                "title": meta.get("title", "Unknown"),
                "page": meta.get("page", "?"),
                "source": meta.get("source", "Unknown")
            })

        print(f"   ✅ Loaded {len(chunks)} chunks")
        return chunks

    def extract_knowledge_from_chunk(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Extract entities and relationships from a single chunk using LLM"""
        text = chunk["text"]

        # Add context from metadata
        context = f"Document: {chunk['title']} (Page {chunk['page']})\n\n{text}"

        prompt = EXTRACTION_PROMPT.format(text=context)

        try:
            response = self.llm.invoke([{"role": "user", "content": prompt}])

            # Parse JSON response
            content = response.content.strip()

            # Clean up markdown code blocks if present
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            result = json.loads(content)
            return result

        except Exception as e:
            print(f"   ⚠️  Error extracting from chunk {chunk['id']}: {e}")
            return {"entities": [], "relationships": []}

    def build_graph_from_knowledge(self, all_knowledge: List[Dict[str, Any]]):
        """Build Neo4j graph from extracted knowledge"""
        print("\n🏗️  Building Neo4j graph...")

        with self.driver.session(database=NEO4J_DATABASE) as session:
            total_entities = 0
            total_relationships = 0

            # Process all extracted knowledge
            for knowledge in all_knowledge:
                entities = knowledge.get("entities", [])
                relationships = knowledge.get("relationships", [])

                # Create entities
                for entity in entities:
                    name = entity.get("name", "").strip()
                    entity_type = entity.get("type", "Entity").strip()
                    description = entity.get("description", "").strip()
                    properties = entity.get("properties", {})

                    if not name:
                        continue

                    # Sanitize label (Neo4j label restrictions)
                    label = entity_type.replace(" ", "").replace("-", "")
                    if not label:
                        label = "Entity"

                    # Create node with comprehensive properties
                    session.run(f"""
                    MERGE (e:{label} {{name: $name}})
                    ON CREATE SET
                        e.description = $description,
                        e.type = $entity_type,
                        e += $properties
                    ON MATCH SET
                        e.description = CASE
                            WHEN size($description) > size(coalesce(e.description, ''))
                            THEN $description
                            ELSE e.description
                        END,
                        e += $properties
                    """, name=name, description=description, entity_type=entity_type, properties=properties)

                    total_entities += 1

                # Create relationships
                for rel in relationships:
                    source = rel.get("source", "").strip()
                    target = rel.get("target", "").strip()
                    rel_type = rel.get("type", "RELATED_TO").strip()
                    rel_desc = rel.get("description", "").strip()

                    if not source or not target:
                        continue

                    # Sanitize relationship type
                    rel_type = rel_type.upper().replace(" ", "_").replace("-", "_")
                    if not rel_type:
                        rel_type = "RELATED_TO"

                    # Create relationship
                    session.run(f"""
                    MATCH (s {{name: $source}})
                    MATCH (t {{name: $target}})
                    MERGE (s)-[r:{rel_type}]->(t)
                    ON CREATE SET r.description = $description
                    """, source=source, target=target, description=rel_desc)

                    total_relationships += 1

            print(f"   ✅ Created {total_entities} entity references")
            print(f"   ✅ Created {total_relationships} relationship references")

            # Get unique counts
            result = session.run("""
            MATCH (n)
            RETURN count(DISTINCT n) as node_count
            """)
            node_count = result.single()["node_count"]

            result = session.run("""
            MATCH ()-[r]->()
            RETURN count(DISTINCT r) as rel_count
            """)
            rel_count = result.single()["rel_count"]

            print(f"\n📊 Final Graph Statistics:")
            print(f"   Unique Nodes: {node_count}")
            print(f"   Unique Relationships: {rel_count}")

    def print_graph_stats(self):
        """Print detailed graph statistics"""
        with self.driver.session(database=NEO4J_DATABASE) as session:
            print("\n" + "="*70)
            print("📊 DETAILED GRAPH STATISTICS")
            print("="*70)

            # Nodes by label
            result = session.run("""
            MATCH (n)
            RETURN labels(n)[0] as label, count(n) as count
            ORDER BY count DESC
            """)

            print("\n🔵 Nodes by Type:")
            for record in result:
                print(f"   {record['label']}: {record['count']}")

            # Relationships by type
            result = session.run("""
            MATCH ()-[r]->()
            RETURN type(r) as rel_type, count(r) as count
            ORDER BY count DESC
            """)

            print("\n🔗 Relationships by Type:")
            for record in result:
                print(f"   {record['rel_type']}: {record['count']}")

            # Sample entities with descriptions
            result = session.run("""
            MATCH (n)
            WHERE n.description IS NOT NULL
            RETURN labels(n)[0] as label, n.name as name,
                   substring(n.description, 0, 100) as desc_preview
            LIMIT 5
            """)

            print("\n📝 Sample Entities (with descriptions):")
            for record in result:
                print(f"   {record['label']}: {record['name']}")
                print(f"      {record['desc_preview']}...")

            print("\n" + "="*70)


def main():
    """Main execution"""
    print("="*70)
    print("🏗️  BUILD KNOWLEDGE GRAPH FROM FAISS CHUNKS")
    print("="*70)
    print("\nThis will:")
    print("  1. Load all chunks from FAISS database")
    print("  2. Extract entities & relationships using LLM")
    print("  3. Build comprehensive Neo4j knowledge graph")
    print("  4. Enable graph-only querying with detailed answers")
    print("="*70 + "\n")

    builder = GraphBuilder()

    try:
        # Step 1: Load chunks
        chunks = builder.load_chunks_from_faiss()

        if not chunks:
            print("❌ No chunks found in FAISS database")
            return

        print(f"\n📊 Found {len(chunks)} chunks across documents")

        # Count by document
        from collections import Counter
        doc_counter = Counter(chunk["title"] for chunk in chunks)
        print("\n📚 Chunks by document:")
        for doc, count in doc_counter.items():
            print(f"   • {doc}: {count} chunks")

        # Ask to clear graph
        response = input("\n❓ Clear existing Neo4j graph? (yes/no): ").strip().lower()
        if response == "yes":
            builder.clear_graph()

        # Ask how many chunks to process (for testing)
        print(f"\n💡 You have {len(chunks)} total chunks")
        response = input("Process all chunks or limit for testing? (all/number): ").strip().lower()

        if response == "all":
            chunks_to_process = chunks
        else:
            try:
                limit = int(response)
                chunks_to_process = chunks[:limit]
                print(f"   Processing first {limit} chunks")
            except:
                chunks_to_process = chunks[:10]
                print(f"   Processing first 10 chunks (default)")

        # Step 2: Extract knowledge from chunks
        print(f"\n🤖 Extracting knowledge from {len(chunks_to_process)} chunks...")
        print("   (This may take a few minutes...)\n")

        all_knowledge = []
        for i, chunk in enumerate(chunks_to_process, 1):
            print(f"   [{i}/{len(chunks_to_process)}] Processing: {chunk['title']} p.{chunk['page']}", end="")

            knowledge = builder.extract_knowledge_from_chunk(chunk)
            all_knowledge.append(knowledge)

            entity_count = len(knowledge.get("entities", []))
            rel_count = len(knowledge.get("relationships", []))
            print(f" → {entity_count} entities, {rel_count} relationships")

        # Step 3: Build graph
        builder.build_graph_from_knowledge(all_knowledge)

        # Step 4: Show statistics
        builder.print_graph_stats()

        print("\n" + "="*70)
        print("✅ GRAPH BUILD COMPLETE!")
        print("="*70)
        print("\n💡 Next steps:")
        print("   1. View graph in Neo4j Browser: http://localhost:7474")
        print("   2. Run query_graph_only.py to test graph-only queries")
        print("   3. Compare with parent-child results")
        print("\n📊 Visualization query:")
        print("   MATCH (n)")
        print("   WHERE n.description IS NOT NULL")
        print("   OPTIONAL MATCH (n)-[r]->(m)")
        print("   RETURN n, r, m LIMIT 100")
        print("="*70)

    finally:
        builder.close()


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not set")
        exit(1)

    if not os.getenv("NEO4J_PASSWORD"):
        print("❌ Error: NEO4J_PASSWORD not set")
        exit(1)

    main()
