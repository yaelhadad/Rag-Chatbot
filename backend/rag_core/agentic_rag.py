from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from neo4j import GraphDatabase
from rag_core.parent_child import ParentChildRAG
from rag_core.utils.entropy_calculator import EntropyCalculator


class AgenticRAG:
    def __init__(self, config):
        # Neo4j driver
        self.driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USERNAME, config.NEO4J_PASSWORD)
        )

        # OpenAI components
        self.embedder = OpenAIEmbeddings(model=config.EMBED_MODEL)
        self.llm = ChatOpenAI(model=config.CHAT_MODEL_ADVANCED, temperature=0.1)

        # Parent-Child RAG for tool
        self.parent_child_rag = ParentChildRAG(config)

        # Entropy calculator
        self.entropy_calculator = EntropyCalculator()
        self._last_entropy_result = {}  # Cache for entropy results
        self._last_chunks_count = 0  # Track chunks from parent_child_search

        # Config
        self.config = config

        # Create tools
        self.tools = self._create_tools()

    def query(self, question: str, max_iterations: int = 5) -> dict:
        # Create agent executor with custom max_iterations
        agent_executor = self._create_agent(max_iterations)

        # Execute agent
        result = agent_executor.invoke({
            "input": question,
            "chat_history": []
        })

        # Parse agent steps from result
        agent_steps = []
        if "intermediate_steps" in result:
            for action, observation in result["intermediate_steps"]:
                agent_steps.append({
                    "tool": action.tool,
                    "input": action.tool_input,
                    "output": observation
                })

        return {
            "answer": result["output"],
            "sources": self._extract_sources(agent_steps),
            "metadata": {
                "agent_steps": agent_steps,
                "iterations": len(agent_steps),
                "model_used": self.config.CHAT_MODEL_ADVANCED,
                "parent_chunks_retrieved": self._last_chunks_count
            }
        }

    def _create_tools(self) -> list:
        # Tool 1: Graph Search (Neo4j)
        graph_tool = Tool(
            name="graph_search",
            func=self._graph_search,
            description="Search knowledge graph for entity relationships. Pass your question or keywords - the tool will extract relevant terms (SSO, SAML, JWT, token, authentication, etc.) and find how they connect in the graph. Use when you need to understand how concepts relate to each other."
        )

        # Tool 2: Parent-Child Search
        parent_child_tool = Tool(
            name="parent_child_search",
            func=self._parent_child_search,
            description="Search documentation for explanations, definitions, and code examples. Use for: 'What is X?', 'Explain X', 'How does X work?', 'How do I implement X?'. Returns complete context from documents."
        )

        # Tool 3: Query Entropy Analyzer
        entropy_tool = Tool(
            name="query_entropy_analyzer",
            func=self._analyze_query_entropy,
            description="Analyze query complexity using Shannon entropy and provide recommendations on which tools to use. Use when you're uncertain about the best approach or want to measure query complexity."
        )

        # Tool 4: Password Strength Analyzer
        password_tool = Tool(
            name="password_strength_analyzer",
            func=self._analyze_password_strength,
            description="Analyze password strength using Shannon entropy. Use when users ask about password security, strength, or want to check if a password is secure. Returns entropy score, strength rating, and recommendations."
        )

        return [graph_tool, parent_child_tool, entropy_tool, password_tool]

    def _create_agent(self, max_iterations: int = 5):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a RAG-powered assistant that MUST use tools to answer questions.

MANDATORY: You MUST use parent_child_search for ANY question asking "What is X?" or "Explain X" - this searches the documentation.

TOOL SELECTION (use ALL relevant tools):
- "What is X?" / "Explain X" / "How does X work?" → MUST use parent_child_search
- "How do I implement/configure/setup..." → MUST use parent_child_search  
- "connects to" / "relates to" / "relationships" → MUST use graph_search
- "Is this password secure?" → MUST use password_strength_analyzer

CRITICAL: For multi-part questions, you MUST use MULTIPLE tools:
- Question: "What is Magic Link, how does it connect to JWT, is password X secure?"
- You MUST call: parent_child_search("What is Magic Link authentication")
- You MUST call: graph_search("Magic Link JWT connection")
- You MUST call: password_strength_analyzer("X")

DO NOT skip parent_child_search - it provides documentation context that graph_search does not have.
DO NOT answer from general knowledge - ONLY from tool results."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        agent = create_openai_functions_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=max_iterations,
            return_intermediate_steps=True  # CRITICAL: Capture tool usage for sources
        )

    def _graph_search(self, query: str) -> str:
        """Search Neo4j knowledge graph for entity relationships"""
        # Extract keywords from query (fix: agent passes full question, not just entity name)
        keywords = self._extract_search_keywords(query)
        
        if not keywords:
            return "No searchable keywords found in the query."
        
        all_relationships = []
        
        with self.driver.session() as session:
            for keyword in keywords:
                cypher_query = """
                MATCH (n)-[r]->(m)
                WHERE toLower(n.name) CONTAINS toLower($search_term)
                   OR toLower(m.name) CONTAINS toLower($search_term)
                RETURN DISTINCT n.name AS source, type(r) AS relationship, m.name AS target
                LIMIT 5
                """
                result = session.run(cypher_query, search_term=keyword)
                
                for record in result:
                    rel = f"{record['source']} -[{record['relationship']}]-> {record['target']}"
                    if rel not in all_relationships:
                        all_relationships.append(rel)
        
        if all_relationships:
            return f"Found relationships (searched: {', '.join(keywords)}):\n" + "\n".join(all_relationships[:15])
        else:
            return f"No relationships found for keywords: {', '.join(keywords)}"
    
    def _extract_search_keywords(self, query: str) -> list:
        """Extract meaningful keywords from query for graph search"""
        # Common technical terms to look for in Frontegg context
        tech_terms = {
            'sso', 'saml', 'oidc', 'oauth', 'jwt', 'token', 'magic link', 'magiclink',
            'passwordless', 'authentication', 'authorization', 'mfa', '2fa',
            'session', 'cookie', 'refresh', 'access', 'identity', 'provider',
            'frontegg', 'user', 'login', 'logout', 'signup', 'email', 'password',
            'api', 'endpoint', 'webhook', 'tenant', 'role', 'permission', 'scope'
        }
        
        query_lower = query.lower()
        found_terms = []
        
        # Check for multi-word terms first
        for term in sorted(tech_terms, key=len, reverse=True):
            if term in query_lower and term not in found_terms:
                found_terms.append(term)
        
        # If no tech terms found, extract capitalized words or nouns
        if not found_terms:
            words = query.split()
            for word in words:
                clean = word.strip('?.,!:;()[]{}"\'-').lower()
                if len(clean) >= 3 and clean not in {'what', 'how', 'the', 'and', 'for', 'with', 'this', 'that', 'are', 'can', 'does'}:
                    if clean not in found_terms:
                        found_terms.append(clean)
        
        return found_terms[:5]  # Limit to 5 keywords for efficiency

    def _parent_child_search(self, query: str) -> str:
        """Search using child chunks, return parent chunks with complete context"""
        try:
            result = self.parent_child_rag.query(query, top_k=4)
            
            # Track chunks count for metadata
            self._last_chunks_count = result['metadata'].get('parent_chunks_retrieved', 0)
            
            # Format the result for the agent
            answer = result['answer']
            sources = result['sources']
            
            formatted = f"Answer: {answer}\n\nSources ({len(sources)} chunks):\n"
            for i, source in enumerate(sources[:3], 1):  # Limit to top 3 for brevity
                formatted += f"{i}. {source['metadata']['title']} - p.{source['metadata']['page']}\n"
            
            return formatted
        except Exception as e:
            return f"Error searching parent-child store: {str(e)}"

    def _analyze_query_entropy(self, query: str) -> str:
        """Calculate Shannon entropy and recommend tools"""
        result = self.entropy_calculator.analyze_query(query)
        
        # Store result for _extract_sources to use
        self._last_entropy_result = result
        
        return f"""Query Entropy Analysis:
- Entropy Score: {result['entropy']:.3f}
- Complexity: {result['complexity']}
- Character Diversity: {result['char_diversity']:.3f}
- Word Count: {result['word_count']}
- Unique Words: {result['unique_words']}

Recommended Tools: {result['recommendations']}
Reasoning: {result['reasoning']}"""

    def _analyze_password_strength(self, password: str) -> str:
        """Analyze password strength using Shannon entropy"""
        result = self.entropy_calculator.analyze_password_strength(password)
        
        recommendations = "\n".join(f"  - {r}" for r in result['recommendations'])
        
        return f"""Password Strength Analysis:
- Password Length: {result['length']} characters
- Shannon Entropy: {result['entropy']} bits
- Strength Rating: {result['strength'].upper()}
- Security Score: {result['score']}/100

Character Types ({result['char_types']}/4):
  - Uppercase (A-Z): {'✓' if result['has_upper'] else '✗'}
  - Lowercase (a-z): {'✓' if result['has_lower'] else '✗'}
  - Numbers (0-9): {'✓' if result['has_digit'] else '✗'}
  - Symbols (!@#$): {'✓' if result['has_symbol'] else '✗'}

Recommendations:
{recommendations}"""

    def _extract_sources(self, agent_steps: list) -> list:
        """Extract sources from agent steps with human-readable tool names"""
        # Tool name mapping for display
        tool_names = {
            'graph_search': 'Knowledge Graph Search',
            'parent_child_search': 'Document Search (Parent-Child RAG)',
            'query_entropy_analyzer': 'Query Complexity Analyzer',
            'password_strength_analyzer': 'Password Strength Analyzer'
        }

        sources = []
        for step in agent_steps:
            tool = step['tool']
            output = step['output']
            tool_display_name = tool_names.get(tool, tool)

            if tool == 'query_entropy_analyzer':
                # Include structured entropy data for frontend display
                entropy_data = getattr(self, '_last_entropy_result', {})
                sources.append({
                    "type": "entropy_analysis",
                    "tool": tool,
                    "tool_name": tool_display_name,
                    "content": output,
                    "entropy": entropy_data.get('entropy', 0),
                    "complexity": entropy_data.get('complexity', 'unknown'),
                    "char_diversity": entropy_data.get('char_diversity', 0),
                    "word_count": entropy_data.get('word_count', 0),
                    "unique_words": entropy_data.get('unique_words', 0),
                    "recommendations": entropy_data.get('recommendations', ''),
                    "reasoning": entropy_data.get('reasoning', '')
                })
            elif tool == 'password_strength_analyzer':
                sources.append({
                    "type": "password_analysis",
                    "tool": tool,
                    "tool_name": tool_display_name,
                    "content": output
                })
            elif tool == 'graph_search':
                sources.append({
                    "type": "graph",
                    "tool": tool,
                    "tool_name": tool_display_name,
                    "content": output
                })
            elif tool == 'parent_child_search':
                sources.append({
                    "type": "parent_child",
                    "tool": tool,
                    "tool_name": tool_display_name,
                    "content": output
                })

        return sources

    def __del__(self):
        """Close Neo4j driver on cleanup"""
        if hasattr(self, 'driver'):
            self.driver.close()

