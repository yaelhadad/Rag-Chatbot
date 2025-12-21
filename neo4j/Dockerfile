# Neo4j Dockerfile for RAG Chatbot
FROM neo4j:5.14-community

# Set working directory
WORKDIR /var/lib/neo4j

# Copy custom configuration if needed
# COPY neo4j.conf /var/lib/neo4j/conf/neo4j.conf

# Copy initialization scripts (optional)
# COPY init-scripts/ /docker-entrypoint-initdb.d/

# Expose ports
EXPOSE 7474 7687

# Health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=5 \
    CMD cypher-shell -u neo4j -p ${NEO4J_PASSWORD:-password} "RETURN 1" || exit 1

# Use default Neo4j entrypoint
# Neo4j image already has proper entrypoint configured

