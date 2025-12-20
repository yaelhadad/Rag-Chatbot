from flask import Blueprint, request, jsonify
import time
import sys
from pathlib import Path

# Add rag_core and rag_api to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from rag_core.simple_vector import SimpleVectorRAG
from rag_core.parent_child import ParentChildRAG
from rag_core.agentic_rag import AgenticRAG
from rag_api.config import Config

query_bp = Blueprint('query', __name__)
config = Config()

# Initialize RAG methods once
rag_methods = {
    1: SimpleVectorRAG(config),
    2: ParentChildRAG(config),
    3: AgenticRAG(config)
}

METHOD_NAMES = {
    1: "Simple Vector RAG",
    2: "Parent-Child Chunk Aware RAG",
    3: "Agentic RAG"
}

@query_bp.route('/query', methods=['POST', 'OPTIONS'])
def handle_query():
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return jsonify({"message": "OK"}), 200
    
    # 1. Validate request
    data = request.get_json()
    if not data:
        return jsonify({
            "success": False,
            "error": {"code": "INVALID_REQUEST", "message": "Request body must be JSON"}
        }), 400
    
    method_id = data.get('method_id')
    question = data.get('question')

    if not method_id or not question:
        return jsonify({
            "success": False,
            "error": {"code": "MISSING_PARAMS", "message": "method_id and question are required"}
        }), 400

    if method_id not in [1, 2, 3]:
        return jsonify({
            "success": False,
            "error": {"code": "INVALID_METHOD", "message": "method_id must be 1, 2, or 3"}
        }), 400

    # 2. Execute RAG method
    try:
        start_time = time.time()
        result = rag_methods[method_id].query(question)
        execution_time = (time.time() - start_time) * 1000

        # 3. Format response
        sources = result["sources"]
        return jsonify({
            "success": True,
            "method_id": method_id,
            "method_name": METHOD_NAMES[method_id],
            "answer": result["answer"],
            "sources": sources,
            "source_count": len(sources),  # Count for UI display "Sources (N)"
            "execution_time_ms": execution_time,
            "metadata": result["metadata"]
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": {
                "code": "EXECUTION_ERROR",
                "message": str(e)
            }
        }), 500

