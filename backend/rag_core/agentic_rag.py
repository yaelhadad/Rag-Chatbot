from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from neo4j import GraphDatabase
from rag_core.parent_child import ParentChildRAG
from rag_core.utils.entropy_calculator import EntropyCalculator


class AgenticRAG:
    def __init__(self, config):
        # Store Neo4j config (lazy connection - only connect when needed)
        self.neo4j_uri = config.NEO4J_URI
        self.neo4j_username = config.NEO4J_USERNAME
        self.neo4j_password = config.NEO4J_PASSWORD
        self._driver = None  # Will be created on first use

        # Set OpenAI API key in environment if not already set
        import os
        if config.OPENAI_API_KEY and not os.getenv("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
        
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
    
    def _get_driver(self):
        """Lazy initialization of Neo4j driver - only connect when needed"""
        if self._driver is None:
            if not self.neo4j_uri:
                raise ValueError(
                    "Neo4j connection not configured. Please set NEO4J_URI, "
                    "NEO4J_USERNAME, and NEO4J_PASSWORD in your .env file."
                )
            self._driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_username, self.neo4j_password)
            )
        return self._driver

    def query(self, question: str, max_iterations: int = 5) -> dict:
        # For now, use simple RAG without complex agent logic
        # This ensures the system works while we fix the agent implementation

        # Try to use parent-child search for documentation questions
        if any(keyword in question.lower() for keyword in ["what", "how", "explain", "definition", "guide"]):
            try:
                result = self.parent_child_rag.query(question, top_k=4)
                # Track chunks count for metadata
                self._last_chunks_count = result['metadata'].get('parent_chunks_retrieved', 0)

                return {
                    "answer": result["answer"],
                    "sources": result["sources"],
                    "metadata": {
                        "agent_steps": [],
                        "iterations": 0,
                        "model_used": self.config.CHAT_MODEL_ADVANCED,
                        "parent_chunks_retrieved": self._last_chunks_count,
                        "strategy": "simplified_agent_parent_child"
                    }
                }
            except Exception as e:
                print(f"Parent-child search failed: {e}")

        # Fallback: simple direct LLM response
        try:
            from langchain_core.prompts import ChatPromptTemplate
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful assistant for Frontegg documentation. Answer based on your knowledge."),
                ("human", "{question}")
            ])

            chain = prompt | self.llm
            response = chain.invoke({"question": question})

            return {
                "answer": response.content,
                "sources": [],
                "metadata": {
                    "agent_steps": [],
                    "iterations": 0,
                    "model_used": self.config.CHAT_MODEL_ADVANCED,
                    "parent_chunks_retrieved": 0,
                    "strategy": "direct_llm"
                }
            }
        except Exception as e:
            return {
                "answer": f"Error: {str(e)}",
                "sources": [],
                "metadata": {
                    "agent_steps": [],
                    "iterations": 0,
                    "model_used": self.config.CHAT_MODEL_ADVANCED,
                    "parent_chunks_retrieved": 0,
                    "strategy": "error"
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

    def _create_agent(self):
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
        from langchain_core.messages import SystemMessage
        from langchain.agents import create_tool_calling_agent

        # Create the prompt template
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
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # Create a simple agent that uses tools directly
        # We'll implement a custom agent that can use tools
        from langchain_core.runnables import RunnablePassthrough
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
        from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
        from langchain_core.tools import tool

        # Create a custom agent that can handle tool calls
        def create_custom_agent():
            def agent_function(input_dict):
                # Get user input
                user_input = input_dict["input"]
                chat_history = input_dict.get("chat_history", [])

                # Create messages
                messages = chat_history + [HumanMessage(content=user_input)]

                # Get LLM response
                response = self.llm.invoke(messages)

                # Check if the response has tool calls
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    # Return the tool calls for execution
                    return {
                        "output": response.content,
                        "tool_calls": response.tool_calls,
                        "intermediate_steps": []
                    }
                else:
                    # Return the final answer
                    return {
                        "output": response.content,
                        "tool_calls": [],
                        "intermediate_steps": []
                    }

            return RunnablePassthrough.assign(output=agent_function)

        # For now, return a simple agent that can be invoked
        # We'll enhance this later with proper tool execution
        return create_custom_agent()

    def _graph_search(self, query: str) -> str:
        """Search Neo4j knowledge graph for entity relationships"""
        # Extract keywords from query (fix: agent passes full question, not just entity name)
        keywords = self._extract_search_keywords(query)
        
        if not keywords:
            return "No searchable keywords found in the query."
        
        all_relationships = []
        
        driver = self._get_driver()
        with driver.session() as session:
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
        if hasattr(self, '_driver') and self._driver is not None:
            self._driver.close()

