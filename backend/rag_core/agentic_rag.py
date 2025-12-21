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
        # Create tool map for O(1) lookup
        self.tool_map = {tool.name: tool.func for tool in self.tools}
    
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
        """
        Execute agentic RAG query using tool calling.
        The LLM decides which tools to use based on the question.
        """
        from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

        # Bind tools to LLM for tool calling
        llm_with_tools = self.llm.bind_tools(self.tools)

        # System prompt for the agent
        system_prompt = """You are an intelligent RAG assistant with access to multiple specialized tools.

CRITICAL RULES - You MUST follow these:
1. ALWAYS use tools to answer questions - NEVER answer from general knowledge alone
2. For "What is X?" or "Explain X" questions → MUST use parent_child_search
3. For "How do I implement/configure X?" questions → MUST use parent_child_search
4. For relationship questions ("How does X connect to Y?") → MUST use graph_search
5. For password security questions → MUST use password_strength_analyzer
6. For multi-part questions → use MULTIPLE tools (one per part)

Tool Usage Examples:
- "What is Magic Link?" → parent_child_search("What is Magic Link authentication?")
- "How does SSO relate to SAML?" → graph_search("SSO SAML relationship")
- "Is password123 secure?" → password_strength_analyzer("password123")
- "What is SSO and how does it connect to SAML?" → parent_child_search("What is SSO?") + graph_search("SSO SAML")

After using tools, synthesize the information into a coherent answer with proper citations."""

        # Initialize conversation
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]

        agent_steps = []
        iteration = 0

        # Agent loop
        while iteration < max_iterations:
            iteration += 1

            # Get LLM response with potential tool calls
            response = llm_with_tools.invoke(messages)

            # Add AI message to conversation
            messages.append(response)

            # Check if LLM made tool calls
            if not response.tool_calls:
                # No more tool calls - this is the final answer
                final_answer = response.content

                # Extract sources from agent steps
                sources = self._extract_sources(agent_steps)

                return {
                    "answer": final_answer,
                    "sources": sources,
                    "metadata": {
                        "agent_steps": [{"tool": s["tool"], "output": s["output"][:200]} for s in agent_steps],
                        "iterations": iteration,
                        "model_used": self.config.CHAT_MODEL_ADVANCED,
                        "tools_used": [s["tool"] for s in agent_steps],
                        "strategy": "full_agent"
                    }
                }

            # Execute tool calls
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_id = tool_call["id"]

                # Execute the tool using O(1) lookup
                tool_func = self.tool_map.get(tool_name)

                if tool_func:
                    try:
                        # Get the first argument (most tools take a single string arg)
                        arg_value = list(tool_args.values())[0] if tool_args else question
                        tool_output = tool_func(arg_value)

                        # Track the step
                        agent_steps.append({
                            "tool": tool_name,
                            "input": arg_value,
                            "output": tool_output
                        })
                    except Exception as e:
                        tool_output = f"Error executing {tool_name}: {str(e)}"
                        agent_steps.append({
                            "tool": tool_name,
                            "input": str(tool_args),
                            "output": tool_output
                        })
                else:
                    tool_output = f"Tool {tool_name} not found"
                    agent_steps.append({
                        "tool": tool_name,
                        "input": str(tool_args),
                        "output": tool_output
                    })

                # Add tool result to conversation
                messages.append(ToolMessage(
                    content=str(tool_output),
                    tool_call_id=tool_id
                ))

        # Max iterations reached - return what we have
        final_answer = f"Maximum iterations ({max_iterations}) reached. Based on tool results:\n\n"
        for step in agent_steps:
            final_answer += f"[{step['tool']}]: {step['output'][:200]}...\n\n"

        sources = self._extract_sources(agent_steps)

        return {
            "answer": final_answer,
            "sources": sources,
            "metadata": {
                "agent_steps": [{"tool": s["tool"], "output": s["output"][:200]} for s in agent_steps],
                "iterations": iteration,
                "model_used": self.config.CHAT_MODEL_ADVANCED,
                "tools_used": [s["tool"] for s in agent_steps],
                "strategy": "full_agent_max_iterations"
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

